import type { Config } from 'tailwindcss'

// Tailwind is used only for spacing/layout utilities. Colors, fonts and
// shapes come from the Phantom UI tokens in src/design-system/tokens.css.
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: 'var(--ink)',
        paper: 'var(--paper)',
        blood: 'var(--blood)',
        'blood-deep': 'var(--blood-deep)',
        ash: 'var(--ash)',
        chalk: 'var(--chalk)',
        gold: 'var(--gold)',
      },
      fontFamily: {
        display: ['Anton', 'Impact', 'sans-serif'],
        ui: ['Barlow', 'system-ui', 'sans-serif'],
        cond: ['"Barlow Condensed"', 'Barlow', 'sans-serif'],
      },
    },
  },
  plugins: [],
} satisfies Config
