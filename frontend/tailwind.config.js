/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        serif: ['Crimson Text', 'Georgia', 'serif'],
      },
      colors: {
        kaya: {
          bg: 'rgb(var(--kaya-bg) / <alpha-value>)',
          surface: 'rgb(var(--kaya-surface) / <alpha-value>)',
          text: 'rgb(var(--kaya-text) / <alpha-value>)',
          muted: 'rgb(var(--kaya-muted) / <alpha-value>)',
          border: 'rgb(var(--kaya-border) / <alpha-value>)',
          gold: 'rgb(var(--kaya-gold) / <alpha-value>)',
          'gold-light': 'rgb(var(--kaya-gold-light) / <alpha-value>)',
          success: 'rgb(var(--kaya-success) / <alpha-value>)',
          error: 'rgb(var(--kaya-error) / <alpha-value>)',
          wood: 'rgb(var(--kaya-wood) / <alpha-value>)',
        },
      },
      keyframes: {
        'fade-in': {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-up': {
          '0%': { opacity: '0', transform: 'translateY(24px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'fade-in': 'fade-in 0.3s ease-out',
        'slide-up': 'slide-up 0.35s ease-out',
      },
    },
  },
  plugins: [],
}
