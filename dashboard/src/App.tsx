import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Categories from './pages/Categories'
import Config from './pages/Config'
import Overview from './pages/Overview'
import Prompts from './pages/Prompts'
import Login from './pages/Login'
import ChangePassword from './pages/ChangePassword'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/change-password" element={
          <ProtectedRoute>
            <ChangePassword />
          </ProtectedRoute>
        } />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <Layout>
                <Routes>
                  <Route path="/" element={<Navigate to="/overview" replace />} />
                  <Route path="/overview" element={<Overview />} />
                  <Route path="/categories" element={<Categories />} />
                  <Route path="/prompts" element={<Prompts />} />
                  <Route path="/config" element={<Config />} />
                </Routes>
              </Layout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App
