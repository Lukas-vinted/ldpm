import { BrowserRouter as Router, Routes, Route, Link, Navigate, useLocation } from 'react-router-dom'
import { LogOut, Moon, Sun } from 'lucide-react'
import { useRef } from 'react'
import Dashboard from './pages/Dashboard'
import DisplaysPage from './pages/DisplaysPage'
import GroupsPage from './pages/GroupsPage'
import SchedulesPage from './pages/SchedulesPage'
import LoginPage from './pages/LoginPage'
import { ThemeProvider, useTheme } from './contexts/ThemeContext'
import './App.css'

function PrivateRoute({ children }: { children: JSX.Element }) {
  const auth = localStorage.getItem('auth');
  const location = useLocation();

  if (!auth) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}

function Navigation() {
  const { theme, toggleTheme } = useTheme();
  const isHandlingClick = useRef(false);
  
  const handleThemeToggle = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (isHandlingClick.current) {
      return;
    }
    
    isHandlingClick.current = true;
    toggleTheme();
    
    setTimeout(() => {
      isHandlingClick.current = false;
    }, 600);
  };
  
  const handleLogout = () => {
    localStorage.removeItem('auth');
    window.location.href = '/login';
  };

  return (
    <nav className="bg-white dark:bg-gray-900 shadow dark:shadow-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">LDPM</h1>
          </div>
          <div className="flex items-center space-x-4">
            <Link to="/" className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white">
              Dashboard
            </Link>
            <Link to="/displays" className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white">
              Displays
            </Link>
            <Link to="/groups" className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white">
              Groups
            </Link>
            <Link to="/schedules" className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white">
              Schedules
            </Link>
            <button
              onClick={handleThemeToggle}
              className="p-2 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-200 active:scale-95"
              aria-label="Toggle theme"
              title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
              type="button"
            >
              {theme === 'light' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
            </button>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}

function App() {
  return (
    <ThemeProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/*"
            element={
              <PrivateRoute>
                <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
                  <Navigation />
                  <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
                    <Routes>
                      <Route path="/" element={<Dashboard />} />
                      <Route path="/displays" element={<DisplaysPage />} />
                      <Route path="/groups" element={<GroupsPage />} />
                      <Route path="/schedules" element={<SchedulesPage />} />
                    </Routes>
                  </main>
                </div>
              </PrivateRoute>
            }
          />
        </Routes>
      </Router>
    </ThemeProvider>
  )
}

export default App
