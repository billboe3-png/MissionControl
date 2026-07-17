'use client'

import { createContext, useContext, useEffect, useState } from 'react'

type Theme = 'light' | 'dark' | 'system'

interface ThemeContextType {
  theme: Theme
  setTheme: (theme: Theme) => void
  resolvedTheme: 'light' | 'dark'
  toggleTheme: () => void
}

const ThemeContext = createContext<ThemeContextType>({
  theme: 'system',
  setTheme: () => {},
  resolvedTheme: 'light',
  toggleTheme: () => {},
})

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>('system')
  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>('light')
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    const stored = localStorage.getItem('theme') as Theme | null
    if (stored) {
      setThemeState(stored)
    }
  }, [])

  useEffect(() => {
    if (!mounted) return

    const root = document.documentElement
    const media = window.matchMedia('(prefers-color-scheme: dark)')

    const update = () => {
      const isDark = theme === 'dark' || (theme === 'system' && media.matches)
      root.classList.toggle('dark', isDark)
      setResolvedTheme(isDark ? 'dark' : 'light')
    }

    update()
    localStorage.setItem('theme', theme)

    media.addEventListener('change', update)
    return () => media.removeEventListener('change', update)
  }, [theme, mounted])

  const setTheme = (t: Theme) => setThemeState(t)
  const toggleTheme = () =>
    setThemeState((prev) => {
      if (prev === 'light') return 'dark'
      if (prev === 'dark') return 'system'
      return 'light'
    })

  if (!mounted) {
    return <>{children}</>
  }

  return (
    <ThemeContext.Provider value={{ theme, setTheme, resolvedTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = () => useContext(ThemeContext)
