/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Enriched CivicFlow Palette:
        // Anchored in user's swatch (#DAD38C, #B3BE7F, #8F9262, #6A7A5D)
        // Boosted in saturation, depth, and contrast for high visibility without neon
        civic: {
          50: '#F7F9F4',     // Fresh, clean, high-clarity canvas
          100: '#EBF1E4',    // Soft vibrant tint for active highlights
          200: '#D5E2C5',    // Distinct border and container tint
          300: '#DAD38C',    // USER BAND 1: Warm Golden Sand / Sage
          400: '#C2CB72',    // Lively olive chartreuse accent
          500: '#9EB356',    // USER BAND 2 (Enriched): Fresh Meadow Sage
          600: '#758843',    // USER BAND 3 (Enriched): Rich Herb Olive
          700: '#486230',    // USER BAND 4 (Enriched): Vibrant Forest Olive
          800: '#32471E',    // Deep high-contrast accent
          900: '#1C2B0E',    // Crisp readable dark text (WCAG AAA)
          950: '#0E1707',    // Deep commanding dark background
        },
        gold: {
          50: '#FFFBEB',
          100: '#FEF3C7',
          200: '#FDE68A',
          300: '#DAD38C',    // Swatch anchor
          400: '#E8B931',
          500: '#D97706',    // Rich warm amber gold
          600: '#B45309',
          700: '#92400E',
        },
        forest: {
          50: '#F0FDF4',
          100: '#DCFCE7',
          200: '#BBF7D0',
          500: '#16A34A',
          600: '#15803D',
          700: '#2A5A24',    // Deep rich forest
          800: '#1E421A',
          900: '#142E11',
        }
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        'civic-sm': '0 1px 3px rgba(42, 90, 36, 0.08), 0 1px 2px rgba(42, 90, 36, 0.04)',
        'civic-md': '0 4px 10px -1px rgba(42, 90, 36, 0.12), 0 2px 6px -1px rgba(42, 90, 36, 0.08)',
        'civic-lg': '0 10px 20px -3px rgba(42, 90, 36, 0.16), 0 4px 8px -2px rgba(42, 90, 36, 0.08)',
        'civic-xl': '0 20px 30px -5px rgba(42, 90, 36, 0.2), 0 10px 12px -5px rgba(42, 90, 36, 0.06)',
      },
    },
  },
  plugins: [],
}
