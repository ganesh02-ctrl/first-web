/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        navy: { 700: "#25336b", 800: "#1e2a5a", 900: "#141c3f" },
        royal: { 500: "#3b5bdb", 600: "#2f4ac0" },
        accent: { 500: "#7c5cd6" },
      },
      boxShadow: { card: "0 1px 3px rgba(16,24,40,.06), 0 1px 2px rgba(16,24,40,.04)" },
    },
  },
  plugins: [],
};
