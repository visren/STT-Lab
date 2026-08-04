import type { Config } from "tailwindcss";

export default {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#071316",
          900: "#0B1F24",
          800: "#123038",
          700: "#1A4450",
        },
        foam: "#E8F2F0",
        mist: "#A8C5BE",
        ember: "#E08B4F",
        tide: "#3FAE9A",
      },
      fontFamily: {
        display: ["var(--font-display)", "Georgia", "serif"],
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      keyframes: {
        rise: {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseBar: {
          "0%, 100%": { opacity: "0.45" },
          "50%": { opacity: "1" },
        },
        shimmer: {
          "0%": { backgroundPosition: "200% 0" },
          "100%": { backgroundPosition: "-200% 0" },
        },
      },
      animation: {
        rise: "rise 0.55s ease-out both",
        "pulse-bar": "pulseBar 1.4s ease-in-out infinite",
        shimmer: "shimmer 2.2s linear infinite",
      },
    },
  },
  plugins: [],
} satisfies Config;
