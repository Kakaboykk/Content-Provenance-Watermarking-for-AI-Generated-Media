/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#09090b', // zinc-950
        card: '#18181b', // zinc-900
        border: '#27272a', // zinc-800
        primary: {
          DEFAULT: '#6366f1', // indigo-500
          hover: '#4f46e5', // indigo-600
          light: '#818cf8', // indigo-400
        },
        success: '#10b981', // emerald-500
        warning: '#f59e0b', // amber-500
        error: '#ef4444', // red-500
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'pulse-glow': 'pulseGlow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        pulseGlow: {
          '0%, 100%': { opacity: '1', boxShadow: '0 0 15px rgba(99, 102, 241, 0.5)' },
          '50%': { opacity: '.7', boxShadow: '0 0 25px rgba(99, 102, 241, 0.8)' },
        }
      }
    },
  },
  plugins: [],
}
