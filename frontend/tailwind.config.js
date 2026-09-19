/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontSize: {
        xs:   ["0.8rem",  { lineHeight: "1.4" }],
        sm:   ["0.9rem",  { lineHeight: "1.5" }],
        base: ["1rem",    { lineHeight: "1.6" }],
        lg:   ["1.15rem", { lineHeight: "1.5" }],
        xl:   ["1.3rem",  { lineHeight: "1.4" }],
        "2xl":["1.55rem", { lineHeight: "1.3" }],
      },
    },
  },
  plugins: [],
};