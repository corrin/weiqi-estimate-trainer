import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './hooks/useAuth'
import { ThemeProvider } from './hooks/useTheme'
import Splash from './pages/Splash'
import Play from './pages/Play'
import Leaderboard from './pages/Leaderboard'
import Progress from './pages/Progress'

function RequireAuth({ children }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-kaya-bg">
        <div className="w-8 h-8 border-2 border-kaya-gold border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/" replace />
  }

  return children
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <div className="min-h-screen bg-kaya-bg">
          <Routes>
            <Route path="/" element={<Splash />} />
            <Route
              path="/play"
              element={
                <RequireAuth>
                  <Play />
                </RequireAuth>
              }
            />
            <Route path="/leaderboard" element={<Leaderboard />} />
            <Route
              path="/progress"
              element={
                <RequireAuth>
                  <Progress />
                </RequireAuth>
              }
            />
          </Routes>
        </div>
      </AuthProvider>
    </ThemeProvider>
  )
}
