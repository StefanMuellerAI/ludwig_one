import { Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, Tag, FileText, Settings, LogOut } from 'lucide-react'
import { logout } from '../lib/api'
import Footer from './Footer'
import { Button } from './ui/button'

interface LayoutProps {
  children: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()

  const isActive = (path: string) => {
    return location.pathname === path
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-32">
            <div className="flex">
              <Link to="/" className="flex items-center space-x-3">
                <img
                  src="/logo.png"
                  alt="LudwigOne Logo"
                  className="h-28"
                />
                <span className="text-sm text-gray-500">Admin</span>
              </Link>
              <div className="ml-10 flex space-x-8">
                <Link
                  to="/overview"
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                    isActive('/overview')
                      ? 'border-brand-500 text-gray-900'
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                  }`}
                >
                  <LayoutDashboard className="w-4 h-4 mr-2" />
                  Übersicht
                </Link>
                <Link
                  to="/categories"
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                    isActive('/categories')
                      ? 'border-brand-500 text-gray-900'
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                  }`}
                >
                  <Tag className="w-4 h-4 mr-2" />
                  Kategorien
                </Link>
                <Link
                  to="/prompts"
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                    isActive('/prompts')
                      ? 'border-brand-500 text-gray-900'
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                  }`}
                >
                  <FileText className="w-4 h-4 mr-2" />
                  Prompts
                </Link>
                <Link
                  to="/config"
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                    isActive('/config')
                      ? 'border-brand-500 text-gray-900'
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                  }`}
                >
                  <Settings className="w-4 h-4 mr-2" />
                  Konfiguration
                </Link>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={logout}
                className="text-gray-600 hover:text-gray-900"
              >
                <LogOut className="w-4 h-4 mr-2" />
                Abmelden
              </Button>
              <img
                src="/logo-right.png"
                alt="Partner Logo"
                className="h-20"
              />
            </div>
          </div>
        </div>
      </nav>

      <main className="flex-1 py-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {children}
        </div>
      </main>

      <Footer />
    </div>
  )
}
