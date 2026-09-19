import { createContext, useContext, useState } from 'react'
import type { ReactNode } from 'react'

export type UserRole = 'citizen' | 'emergency_personnel'

interface AuthUser { name: string; role: UserRole }
interface AuthContextType {
  user: AuthUser | null
  role: UserRole | null
  isAuthenticated: boolean
  login: (role: UserRole, name?: string) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextType | null>(null)

// Deliberately local demo state. Replace this provider's implementation with Cognito later.
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  function login(role: UserRole, name = role === 'citizen' ? 'Community member' : 'Operations user') {
    setUser({ name, role })
  }
  function logout() { setUser(null) }
  return <AuthContext.Provider value={{ user, role: user?.role ?? null, isAuthenticated: !!user, login, logout }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}
