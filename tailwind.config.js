/** @type {import('tailwindcss').Config} */
const plugin = require('tailwindcss/plugin')

module.exports = {
  content: [
    './templates/**/*.html',
    './static_files/**/*.css',
    './static_files/**/*.js'
  ],
  plugins: [
    plugin(({ addVariant, addUtilities, matchVariant }) => {
      // Hover media queries
      addVariant("has-hover", "@media (hover: hover) and (pointer: fine)")
      addVariant("no-hover", "@media not all and (hover: hover) and (pointer: fine)")

      // Applied on hover if supported, never applied otherwise
      addVariant("hover-never", "@media (hover: hover) and (pointer: fine) { &:hover }")
      matchVariant(
        "group-hover-never",
        (_, { modifier }) => `@media (hover: hover) and (pointer: fine) { :merge(.group${modifier ? "\\/" + modifier : ""}):hover & }`,
        { values: { DEFAULT: "" } },
      )
      matchVariant(
        "peer-hover-never",
        (_, { modifier }) => `@media (hover: hover) and (pointer: fine) { :merge(.peer${modifier ? "\\/" + modifier : ""}):hover & }`,
        { values: { DEFAULT: "" } },
      )

      // Applied on hover if supported, always applied otherwise
      addVariant("hover-always", [
        "@media (hover: hover) and (pointer: fine) { &:hover }",
        "@media not all and (hover: hover) and (pointer: fine)",
      ])
      matchVariant(
        "group-hover-always",
        (_, { modifier }) => [
            `@media (hover: hover) and (pointer: fine) { :merge(.group${modifier ? "\\/" + modifier : ""}):hover & }`,
            "@media not all and (hover: hover) and (pointer: fine)",
        ],
        { values: { DEFAULT: "" } },
      )
      matchVariant(
        "peer-hover-always",
        (_, { modifier }) => [
            `@media (hover: hover) and (pointer: fine) { :merge(.peer${modifier ? "\\/" + modifier : ""}):hover & }`,
            "@media not all and (hover: hover) and (pointer: fine)",
        ],
        { values: { DEFAULT: "" } },
      )
    }),
  ]
}
