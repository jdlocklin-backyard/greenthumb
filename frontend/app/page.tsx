/**
 * GreenThumb Dashboard Page
 * 
 * Main landing page displaying user's gardens and quick actions.
 */

import { Leaf, Plus, Cloud } from 'lucide-react';

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-green-50 to-white">
      {/* Header */}
      <header className="border-b bg-white shadow-sm">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Leaf className="h-8 w-8 text-green-600" />
            <h1 className="text-2xl font-bold text-gray-900">GreenThumb</h1>
          </div>
          <nav className="flex items-center gap-4">
            <a href="#" className="text-gray-600 hover:text-gray-900">
              My Gardens
            </a>
            <a href="#" className="text-gray-600 hover:text-gray-900">
              Plants
            </a>
            <a href="#" className="text-gray-600 hover:text-gray-900">
              Weather
            </a>
            <button className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700">
              Sign In
            </button>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16">
        <div className="text-center max-w-3xl mx-auto">
          <h2 className="text-5xl font-bold text-gray-900 mb-6">
            Your Personal Garden Assistant
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Manage your gardens, track your plants, and get automated weather updates
            - all self-hosted on your Proxmox home lab.
          </p>
          <div className="flex gap-4 justify-center">
            <button className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 flex items-center gap-2">
              <Plus className="h-5 w-5" />
              Create Your First Garden
            </button>
            <button className="border border-gray-300 text-gray-700 px-6 py-3 rounded-lg hover:bg-gray-50">
              View Documentation
            </button>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="container mx-auto px-4 py-16">
        <div className="grid md:grid-cols-3 gap-8">
          {/* Feature 1 */}
          <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
            <div className="bg-green-100 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
              <Leaf className="h-6 w-6 text-green-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Garden Management
            </h3>
            <p className="text-gray-600">
              Create and manage multiple gardens with GPS coordinates and detailed tracking.
            </p>
          </div>

          {/* Feature 2 */}
          <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
            <div className="bg-blue-100 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
              <Cloud className="h-6 w-6 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Automated Weather
            </h3>
            <p className="text-gray-600">
              Autonomous agent checks weather every 15 minutes using Open-Meteo API.
            </p>
          </div>

          {/* Feature 3 */}
          <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
            <div className="bg-purple-100 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
              <Leaf className="h-6 w-6 text-purple-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Plant Database
            </h3>
            <p className="text-gray-600">
              Track planting dates, varieties, and harvest schedules for all your plants.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t bg-white mt-16">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center text-gray-600">
            <p>&copy; 2024 GreenThumb. Self-hosted on Proxmox.</p>
            <p className="text-sm mt-2">
              Powered by Next.js, FastAPI, and PostgreSQL with PostGIS
            </p>
          </div>
        </div>
      </footer>
    </main>
  );
}
