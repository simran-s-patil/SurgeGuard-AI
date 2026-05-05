export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        apollo: {
          teal: '#0f5e5f',
          yellow: '#ffb700',
          light: '#f7f9fa',
          panel: '#fbfcfd',
          soft: '#e4e8eb',
          warn: '#d72f2f',
          success: '#23a39b',
        },
      },
      boxShadow: {
        panel: '0 18px 45px rgba(15,94,95,0.08)',
      },
    },
  },
  plugins: [],
}
