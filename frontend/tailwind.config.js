/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        darkBg: '#0B0F17',
        darkPanel: '#161B22',
        darkBorder: '#30363D',
        aiBubble: '#21262D',
        userBubble: '#1F6FEB',
      }
    },
  },
  plugins: [],
}
