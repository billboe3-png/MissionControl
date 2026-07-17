'use client'

import { Moon, Sun, Monitor } from 'lucide-react'
import { useTheme } from './ThemeProvider'
import { useEffect, useState } from 'react'

export function ThemeToggle() {
  const { theme, setTheme, resolvedTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => { setMounted(true) }, [])

  if (!mounted) {
    return <div className="w-9 h-9" />
  }

  const cycle = () => {
    if (theme === 'light') setTheme('dark')
    else if (theme === 'dark') setTheme('system')
    else setTheme('light')
  }

  const icon = theme === 'dark' ? Moon : theme === 'light' ? Sun : Monitor

  return (
    <button
      onClick={cycle}
      className="p-2 rounded-lg hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors"
      aria-label={`Current theme: ${theme}. Click to cycle.`}
    >
      {icon === Sun && <Sun className="w-5 h-5" />}
      {icon === Moon && <Moon className="w-5 h-5" />}
      {icon === Monitor && <Monitor className="w-5 h-5" />}
    </button>
  )
}
