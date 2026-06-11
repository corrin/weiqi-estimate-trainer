import { useState, useEffect, createContext, useContext } from 'react'
import { api } from '../api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      api('/me/stats')
        .then(() => {
          setUser({
            email: localStorage.getItem('email'),
            name: localStorage.getItem('name'),
          })
        })
        .catch(() => {
          localStorage.removeItem('token')
          localStorage.removeItem('email')
          localStorage.removeItem('name')
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const loginWithGoogle = async (credential) => {
    const data = await api('/auth/google', {
      method: 'POST',
      body: JSON.stringify({ credential }),
    })
    localStorage.setItem('token', data.token)
    localStorage.setItem('email', data.user.email)
    localStorage.setItem('name', data.user.name)
    setUser(data.user)
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('email')
    localStorage.removeItem('name')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, loginWithGoogle, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
