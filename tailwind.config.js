/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        outfit: ['Outfit', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        themeBg: '#090d16',
        panelBg: 'rgba(18, 26, 43, 0.75)',
        borderDim: 'rgba(255, 255, 255, 0.08)',
        accentBlue: '#3b82f6',
        accentCyan: '#06b6d4',
        accentPurple: '#8b5cf6',
        accentGreen: '#10b981',
        accentRed: '#ef4444',
      }
    },
  },
  plugins: [],
}
