/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: ["./src/**/*.{js,jsx,ts,tsx}", "./public/index.html"],
  theme: {
    extend: {
      colors: {
        // AHD Command OS palette
        bg: { DEFAULT: "#0a0e1a", deep: "#050810", panel: "#0f1423", elev: "#171b2c" },
        ink: { DEFAULT: "#f1f5f9", muted: "#94a3b8", faint: "#64748b" },
        line: { DEFAULT: "rgba(255,255,255,0.06)", strong: "rgba(255,255,255,0.12)" },
        // Primary action — green (operational)
        ok: { DEFAULT: "#22c55e", soft: "#34d399", glow: "rgba(34,197,94,0.18)" },
        // Sovereign accent — indigo (decision tier)
        sov: { DEFAULT: "#6366f1", soft: "#818cf8", glow: "rgba(99,102,241,0.16)" },
        // Other tones
        warn: { DEFAULT: "#fbbf24", soft: "#fde68a" },
        danger: { DEFAULT: "#fb7185", soft: "#fda4af" },
        review: { DEFAULT: "#a78bfa" },
        info: { DEFAULT: "#5aa2ff" },
      },
      fontFamily: {
        display: ['"Space Grotesk"', "ui-sans-serif", "system-ui", "sans-serif"],
        sans: ['"Inter"', "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
      borderRadius: { card: "14px", soft: "10px" },
      boxShadow: {
        card: "0 8px 32px rgba(0,0,0,.32)",
        glow: "0 0 32px rgba(34,197,94,0.10)",
        sov: "0 0 48px rgba(99,102,241,0.18), 0 0 8px rgba(99,102,241,0.08)",
      },
    },
  },
  plugins: [],
};
