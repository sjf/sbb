/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',  // Scan Jinja templates for class usage
    './static/**/*.css'
  ],
  theme: {
    extend: {
      colors: {
        'main': {
          '50': '#fdfde9',
          '100': '#fdfac4',
          '200': '#fbf18d',
          '300': '#f9e353',
          '400': '#f5cf1a',
          '500': '#e5b60d',
          '600': '#c58d09',
          '700': '#9d650b',
          '800': '#825011',
          '900': '#6f4114',
          '950': '#412207',
        },
      },
    },
  },
  plugins: [],
}
