/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',  // Scan Jinja templates for class usage
    './static/**/*.css'
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
