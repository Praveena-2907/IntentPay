/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        console: {
          bg: '#0B0F14',
          dark: '#080C10',
          card: '#111820',
          surface: '#111820',
          'surface-2': '#161F29',
          border: '#1F2A37',
          text: '#E6EDF3',
          muted: '#8B98A5',
          accent: '#3B82F6',
          allow: '#22C55E',
          verify: '#F59E0B',
          hold: '#EF4444',
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      borderRadius: {
        DEFAULT: '4px',
        sm: '2px',
        md: '4px',
        lg: '6px',
      }
    },
  },
  plugins: [],
}
