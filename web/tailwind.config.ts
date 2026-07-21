import type { Config } from "tailwindcss";

/** Semantic palette driven by CSS variables (see styles/index.css) so dark
 * mode is a single class toggle. Channels are space-separated RGB so Tailwind
 * opacity modifiers (e.g. text-ink/70) keep working. */
const c = (v: string) => `rgb(var(${v}) / <alpha-value>)`;

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        paper: c("--paper"),
        surface: c("--surface"),
        "surface-2": c("--surface-2"),
        border: c("--border"),
        ink: c("--ink"),
        muted: c("--muted"),
        accent: c("--accent"),
        "accent-ink": c("--accent-ink"),
        highlight: c("--highlight"),
      },
      fontFamily: {
        serif: ['"Newsreader"', "Georgia", "Cambria", "serif"],
        sans: ['"Inter"', "system-ui", "-apple-system", "sans-serif"],
      },
      maxWidth: {
        reader: "42rem",
      },
      boxShadow: {
        card: "0 1px 2px rgb(28 25 23 / 0.04), 0 8px 24px -12px rgb(28 25 23 / 0.12)",
        "card-hover":
          "0 2px 4px rgb(28 25 23 / 0.06), 0 16px 40px -16px rgb(28 25 23 / 0.22)",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0", transform: "translateY(4px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.4s ease-out both",
        shimmer: "shimmer 1.6s infinite",
      },
    },
  },
  plugins: [],
} satisfies Config;
