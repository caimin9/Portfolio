import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        terminal: {
          bg: '#0a0a0f',
          surface: '#1a1a28',
          border: '#2a2a38',
          accent: '#6366f1',
          success: '#10b981',
          danger: '#ef4444',
          warning: '#f59e0b',
          text: '#e5e7eb',
          muted: '#9ca3af',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Courier New', 'monospace'],
      },
    },
  },
  plugins: [],
}
export default config
