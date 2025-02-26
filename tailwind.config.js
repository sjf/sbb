/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './static_files/**/*.css',
    './static_files/**/*.js'
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
