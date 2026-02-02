/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: '#009bc8',
          50: '#e6f7fb',
          100: '#cceff7',
          200: '#99dfef',
          300: '#66cfe7',
          400: '#33bfdf',
          500: '#009bc8',
          600: '#007ca0',
          700: '#005d78',
          800: '#003e50',
          900: '#001f28',
        },
      },
    },
  },
  plugins: [],
}
