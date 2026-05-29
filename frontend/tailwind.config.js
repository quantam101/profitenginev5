/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}", "./public/index.html"],
  theme: {
    extend: {
      colors: {
        bg: { DEFAULT: "#050505", surface: "#0C0C0C", elev: "#141414" },
        ink: { DEFAULT: "#F3F4F6", muted: "#9CA3AF", faint: "#4B5563" },
        line: { DEFAULT: "#1F2937", subtle: "#111827", live: "#00FF41" },
        acid: { DEFAULT: "#00FF41", soft: "#CCFF00" },
      },
      fontFamily: {
        display: ['"Space Mono"', "ui-monospace", "monospace"],
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
      boxShadow: {
        glow: "0 0 24px rgba(0, 255, 65, 0.35)",
        glowSm: "0 0 12px rgba(0, 255, 65, 0.4)",
      },
    },
  },
  plugins: [],
};
