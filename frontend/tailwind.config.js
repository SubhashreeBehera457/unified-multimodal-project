/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        command: {
          bg: "#0B0F17",
          panel: "#111827",
          panelAlt: "#161E2E",
          border: "#1F2937",
          borderLight: "#374151",
          accent: "#38BDF8",
          accentDim: "#0284C7",
          critical: "#EF4444",
          warning: "#F59E0B",
          safe: "#10B981",
          muted: "#94A3B8",
          text: "#F1F5F9",
        }
      },
      fontFamily: {
        mono: ["JetBrains Mono", "SFMono-Regular", "Menlo", "Monaco", "Consolas", "monospace"],
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
      }
    },
  },
  plugins: [],
}
