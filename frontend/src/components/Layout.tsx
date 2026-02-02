import { Link, useLocation } from 'react-router-dom'
import { Upload, FileText, AlertTriangle } from 'lucide-react'
import Footer from './Footer'

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
              <Link to="/" className="flex items-center">
                <img
                  src="/logo.png"
                  alt="LudwigOne Logo"
                  className="h-28"
                />
              </Link>
              <div className="ml-10 flex space-x-8">
                <Link
                  to="/upload"
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                    isActive('/upload')
                      ? 'border-brand-500 text-gray-900'
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                  }`}
                >
                  <Upload className="w-4 h-4 mr-2" />
                  Hochladen
                </Link>
                <Link
                  to="/jobs"
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                    isActive('/jobs')
                      ? 'border-brand-500 text-gray-900'
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                  }`}
                >
                  <FileText className="w-4 h-4 mr-2" />
                  Aufträge
                </Link>
              </div>
            </div>
            <div className="flex items-center space-x-6">
              <div className="flex items-center bg-red-50 border border-red-200 rounded-lg px-4 py-2 max-w-md">
                <AlertTriangle className="h-5 w-5 text-red-600 flex-shrink-0 mr-2" />
                <p className="text-sm text-red-800 font-medium">
                  <span className="font-bold">Testphase:</span> Bitte keine personenbezogenen Daten hochladen!
                </p>
              </div>
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
