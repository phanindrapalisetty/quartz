export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Ubuntu', 'system-ui', 'sans-serif'],
      },
      colors: {
        brand: {
          DEFAULT: '#1E505F',
          hover:   '#164050',
          light:   '#E8F4F7',
        },
        accent: {
          DEFAULT: '#20A7C9',
          hover:   '#1A93B0',
          light:   '#D7EFF5',
        },
      },
    },
  },
  plugins: [],
}
