/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Sidebar / deep background
        sidebar: {
          DEFAULT: '#1E1B4B',
          hover:   'rgba(255,255,255,0.08)',
          active:  '#4338CA',
        },
        // Primary brand
        indigo: {
          dark:    '#312E81',
          DEFAULT: '#4338CA',
          light:   '#6366F1',
        },
        // Deep purple accent
        violet: {
          DEFAULT: '#7C3AED',
          light:   '#8B5CF6',
          bg:      '#EDE9FE',
        },
        // AI / success accent
        mint: {
          DEFAULT: '#10B981',
          bg:      '#D1FAE5',
          dark:    '#059669',
        },
        // Page background
        bg: {
          DEFAULT: '#F8F7FF',
          card:    '#FFFFFF',
        },
        // Text
        text: {
          primary:   '#1E1B4B',
          secondary: '#6B7280',
          muted:     '#9CA3AF',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Roboto', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        '2xs': ['11px', '16px'],
        'xs':  ['12px', '18px'],
        'sm':  ['13px', '20px'],
        'base':['14px', '22px'],
        'md':  ['15px', '24px'],
        'lg':  ['16px', '26px'],
        'xl':  ['18px', '28px'],
        '2xl': ['20px', '30px'],
        '3xl': ['24px', '32px'],
      },
      borderRadius: {
        sm:  '6px',
        DEFAULT: '8px',
        md:  '8px',
        lg:  '12px',
        xl:  '16px',
      },
      boxShadow: {
        card:   '0 2px 8px rgba(0,0,0,0.08)',
        hover:  '0 6px 20px rgba(0,0,0,0.12)',
        modal:  '0 8px 32px rgba(0,0,0,0.16)',
        sidebar:'4px 0 16px rgba(30,27,75,0.15)',
      },
      animation: {
        'shimmer':    'shimmer 1.6s infinite linear',
        'typing-dot': 'typing-dot 1.2s infinite',
        'slide-in':   'slide-in 0.25s ease-out',
        'fade-in':    'fade-in 0.2s ease-out',
        'float-up':   'float-up 0.2s ease-out',
      },
      keyframes: {
        shimmer: {
          '0%':   { backgroundPosition: '-400px 0' },
          '100%': { backgroundPosition: '400px 0' },
        },
        'typing-dot': {
          '0%, 60%, 100%': { opacity: 0.3, transform: 'scale(0.8)' },
          '30%':           { opacity: 1,   transform: 'scale(1)' },
        },
        'slide-in': {
          from: { opacity: 0, transform: 'translateX(-8px)' },
          to:   { opacity: 1, transform: 'translateX(0)' },
        },
        'fade-in': {
          from: { opacity: 0, transform: 'translateY(4px)' },
          to:   { opacity: 1, transform: 'translateY(0)' },
        },
        'float-up': {
          from: { opacity: 0, transform: 'translateY(8px)' },
          to:   { opacity: 1, transform: 'translateY(0)' },
        },
      },
      transitionProperty: {
        size: 'width, height',
      },
    },
  },
  plugins: [],
}
