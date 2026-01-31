import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import DisplaysPage from './pages/DisplaysPage'
import GroupsPage from './pages/GroupsPage'
import SchedulesPage from './pages/SchedulesPage'
import './App.css'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        {/* Navigation */}
        <nav className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <h1 className="text-xl font-bold text-gray-900">LDPM</h1>
              </div>
              <div className="flex items-center space-x-4">
                <Link to="/" className="text-gray-600 hover:text-gray-900">
                  Dashboard
                </Link>
                <Link to="/displays" className="text-gray-600 hover:text-gray-900">
                  Displays
                </Link>
                <Link to="/groups" className="text-gray-600 hover:text-gray-900">
                  Groups
                </Link>
                <Link to="/schedules" className="text-gray-600 hover:text-gray-900">
                  Schedules
                </Link>
              </div>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/displays" element={<DisplaysPage />} />
            <Route path="/groups" element={<GroupsPage />} />
            <Route path="/schedules" element={<SchedulesPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
