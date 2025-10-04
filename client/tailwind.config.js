/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'tally-blue': '#0052CC',
        'tally-dark': '#1a1d2e',
        'tally-light': '#f8f9fa',
      },
    },
  },
  plugins: [],
}
