/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      colors: {
        // brand = emerald (recovery / success / money coming back)
        brand: {
          50: '#ecfdf5', 100: '#d1fae5', 200: '#a7f3d0', 300: '#6ee7b7',
          400: '#34d399', 500: '#10b981', 600: '#059669', 700: '#047857',
          800: '#065f46', 900: '#064e3b', 950: '#022c22',
        },
        // accent = violet/indigo (secondary highlight — nav, focus, links, agents)
        accent: {
          50: '#f5f3ff', 100: '#ede9fe', 200: '#ddd6fe', 300: '#c4b5fd',
          400: '#a78bfa', 500: '#8b5cf6', 600: '#7c3aed', 700: '#6d28d9',
          800: '#5b21b6', 900: '#4c1d95', 950: '#2e1065',
        },
        // danger = rose (blocked / rejected / failed)
        danger: {
          50: '#fef2f2', 100: '#fee2e2', 200: '#fecaca', 300: '#fca5a5',
          400: '#fb7185', 500: '#f43f5e', 600: '#e11d48', 700: '#be123c',
          800: '#9f1239', 900: '#881337', 950: '#4c0519',
        },
        // warning = amber (escalated / in progress)
        warning: {
          50: '#fffbeb', 100: '#fef3c7', 200: '#fde68a', 300: '#fcd34d',
          400: '#fbbf24', 500: '#f59e0b', 600: '#d97706', 700: '#b45309',
          800: '#92400e', 900: '#78350f', 950: '#451a03',
        },
        // surface = deep slate (backgrounds — cooler & richer than plain gray)
        surface: {
          50: '#f8fafc', 100: '#eef1f6', 200: '#dfe3ea', 300: '#c3c9d4',
          400: '#8b93a5', 500: '#5c6479', 600: '#3f465a', 700: '#2a3040',
          800: '#1a1f2c', 900: '#12151e', 950: '#0a0c13',
        },
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(16,185,129,0.15), 0 8px 24px -8px rgba(16,185,129,0.45)',
        'glow-accent': '0 0 0 1px rgba(139,92,246,0.15), 0 8px 24px -8px rgba(139,92,246,0.45)',
        card: '0 1px 0 0 rgba(255,255,255,0.03) inset, 0 12px 32px -16px rgba(0,0,0,0.6)',
      },
      backgroundImage: {
        'grid-glow':
          'radial-gradient(ellipse 80% 50% at 15% -10%, rgba(16,185,129,0.16), transparent 60%), radial-gradient(ellipse 60% 40% at 100% 0%, rgba(139,92,246,0.14), transparent 60%)',
      },
    },
  },
  plugins: [],
}
