/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',  // Scan Jinja templates for class usage
    './static/**/*.css'
  ],
  theme: {
    extend: {
      colors: {
        /*'yellow': {
          '400': '#ffd76f',
        },*/
      },
    },
  },
  plugins: [],
}
