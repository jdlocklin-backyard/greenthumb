"""
Autonomous Agent Worker

Scheduled tasks for weather data collection and seed database synchronization.
Uses APScheduler with Redis backend for distributed locking.
"""

import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import httpx
import redis
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv
from pythonjsonlogger import jsonlogger
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()


class JSONFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter for structured logging.
    
    Ensures consistent log format with ISO 8601 timestamps and
    additional context fields for production observability.
    """
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """
        Add custom fields to log record.
        
        Args:
            log_record: The log record being built.
            record: Original LogRecord object.
            message_dict: Message dictionary.
        """
        super().add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['service'] = 'agent'


def setup_logging() -> None:
    """
    Configure structured JSON logging for the agent.
    
    All logs output to stdout in JSON format for easy parsing
    by log aggregation systems.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler(sys.stdout)
    formatter = JSONFormatter('%(timestamp)s %(level)s %(name)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def get_redis_client() -> redis.Redis:
    """
    Create Redis client for task locking.
    
    Returns:
        Configured Redis client.
        
    Raises:
        redis.RedisError: If connection fails.
    """
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        password=os.getenv("REDIS_PASSWORD"),
        decode_responses=True
    )


def get_database_engine():
    """
    Create SQLAlchemy engine for database access.
    
    Returns:
        Configured SQLAlchemy engine.
        
    Raises:
        sqlalchemy.exc.SQLAlchemyError: If connection fails.
    """
    database_url = os.getenv("DATABASE_URL")
    return create_engine(database_url, pool_pre_ping=True)


async def fetch_weather_data(latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
    """
    Fetch weather data from Open-Meteo API.
    
    Uses Open-Meteo free API for weather forecasts.
    No API key required.
    
    Args:
        latitude: Geographic latitude.
        longitude: Geographic longitude.
        
    Returns:
        Weather data dictionary or None if fetch fails.
        
    Raises:
        httpx.HTTPError: On network or API errors.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": True,
        "hourly": "temperature_2m,relativehumidity_2m,precipitation,windspeed_10m"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logging.error(f"Weather API request failed: {e}")
        return None


def weather_check_job() -> None:
    """
    Scheduled job to check weather for all gardens.
    
    Fetches current weather data from Open-Meteo API and stores
    it in the database for each garden.
    
    Wrapped in try/except to prevent scheduler crash on errors.
    """
    logger = logging.getLogger(__name__)
    redis_client = get_redis_client()
    
    # Distributed lock to prevent multiple agent instances from running simultaneously
    lock_key = "agent:weather_check:lock"
    lock = redis_client.lock(lock_key, timeout=300)  # 5-minute lock
    
    if not lock.acquire(blocking=False):
        logger.info("Weather check already running, skipping")
        return
    
    try:
        logger.info("Starting weather check job")
        engine = get_database_engine()
        
        with engine.connect() as conn:
            # Fetch all gardens with their coordinates
            result = conn.execute(text("""
                SELECT id, latitude, longitude, name
                FROM gardens
                WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            """))
            
            gardens = result.fetchall()
            logger.info(f"Found {len(gardens)} gardens to check weather for")
            
            for garden in gardens:
                garden_id, lat, lng, name = garden
                
                try:
                    # Fetch weather data
                    import asyncio
                    weather_data = asyncio.run(fetch_weather_data(lat, lng))
                    
                    if not weather_data or "current_weather" not in weather_data:
                        logger.warning(f"No weather data for garden {name} ({garden_id})")
                        continue
                    
                    current = weather_data["current_weather"]
                    
                    # Insert weather record
                    conn.execute(text("""
                        INSERT INTO weather (
                            id, garden_id, temperature, humidity, precipitation,
                            wind_speed, condition, recorded_at, created_at
                        )
                        VALUES (
                            gen_random_uuid(), :garden_id, :temperature, :humidity,
                            :precipitation, :wind_speed, :condition, :recorded_at, NOW()
                        )
                    """), {
                        "garden_id": garden_id,
                        "temperature": current.get("temperature", 0),
                        "humidity": weather_data.get("hourly", {}).get("relativehumidity_2m", [0])[0],
                        "precipitation": weather_data.get("hourly", {}).get("precipitation", [0])[0],
                        "wind_speed": current.get("windspeed", 0),
                        "condition": "Clear",  # Open-Meteo uses weathercode, simplified here
                        "recorded_at": datetime.utcnow()
                    })
                    
                    conn.commit()
                    logger.info(f"Stored weather data for garden {name}")
                    
                except Exception as e:
                    logger.error(f"Error processing weather for garden {name}: {e}", exc_info=True)
                    # Continue with next garden despite error
                    continue
        
        logger.info("Weather check job completed successfully")
        
    except Exception as e:
        logger.error(f"Weather check job failed: {e}", exc_info=True)
    finally:
        lock.release()
        logger.info("Released weather check lock")


def seed_database_job() -> None:
    """
    Scheduled job to sync plant data from OpenFoodFacts.
    
    Fetches plant/crop data from OpenFoodFacts API to enrich
    our seed database with scientific names, growth info, etc.
    
    Wrapped in try/except to prevent scheduler crash on errors.
    """
    logger = logging.getLogger(__name__)
    redis_client = get_redis_client()
    
    lock_key = "agent:seed_database:lock"
    lock = redis_client.lock(lock_key, timeout=600)  # 10-minute lock
    
    if not lock.acquire(blocking=False):
        logger.info("Seed database sync already running, skipping")
        return
    
    try:
        logger.info("Starting seed database sync job")
        
        # OpenFoodFacts API endpoint for plant-based products
        # This is a placeholder - actual implementation would fetch
        # botanical data from appropriate sources
        
        logger.info("Seed database sync completed (placeholder)")
        
    except Exception as e:
        logger.error(f"Seed database sync failed: {e}", exc_info=True)
    finally:
        lock.release()
        logger.info("Released seed database lock")


def main() -> None:
    """
    Main entry point for the autonomous agent.
    
    Sets up scheduler, registers jobs, and handles graceful shutdown.
    """
    # Setup structured logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting GreenThumb Agent")
    
    # Verify environment configuration
    required_vars = ["DATABASE_URL", "REDIS_HOST", "REDIS_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)
    
    # Test Redis connection
    try:
        redis_client = get_redis_client()
        redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        sys.exit(1)
    
    # Test database connection
    try:
        engine = get_database_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)
    
    # Create scheduler
    scheduler = BackgroundScheduler()
    
    # Register weather check job
    # Runs every N minutes (configurable via AGENT_CHECK_INTERVAL)
    check_interval = int(os.getenv("AGENT_CHECK_INTERVAL", "15"))
    scheduler.add_job(
        weather_check_job,
        trigger=IntervalTrigger(minutes=check_interval),
        id="weather_check",
        name="Weather Check Job",
        replace_existing=True
    )
    logger.info(f"Registered weather check job (every {check_interval} minutes)")
    
    # Register seed database job
    # Runs once daily at 3 AM
    scheduler.add_job(
        seed_database_job,
        trigger="cron",
        hour=3,
        minute=0,
        id="seed_database",
        name="Seed Database Sync Job",
        replace_existing=True
    )
    logger.info("Registered seed database sync job (daily at 3 AM)")
    
    # Start scheduler
    scheduler.start()
    logger.info("Scheduler started successfully")
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully")
        scheduler.shutdown(wait=True)
        logger.info("Scheduler stopped")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Keep the agent running
    logger.info("Agent is running, waiting for scheduled jobs")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down")
        scheduler.shutdown(wait=True)


if __name__ == "__main__":
    main()
