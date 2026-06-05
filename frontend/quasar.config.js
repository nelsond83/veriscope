import { defineConfig } from '#q-app/wrappers'

export default defineConfig((ctx) => {
  return {
    boot: ['axios'],
    css: ['app.scss'],
    extras: ['material-icons', 'roboto-font'],
    build: {
      target: {
        browser: ['es2019', 'edge88', 'firefox78', 'chrome87', 'safari13.1'],
        node: 'node20',
      },
      vueRouterMode: 'hash',
    },
    devServer: {
      open: true,
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
        '/media': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
    framework: {
      config: {
        dark: true,
        brand: {
          primary: '#22d3ee',
          secondary: '#10b981',
          accent: '#6366f1',
          dark: '#0f172a',
          'dark-page': '#0d1117',
          positive: '#10b981',
          negative: '#ef4444',
          info: '#22d3ee',
          warning: '#f59e0b',
        },
      },
      plugins: ['Notify', 'Dialog', 'Loading'],
    },
    animations: [],
    ssr: { pwa: false },
    pwa: {},
    capacitor: {},
    electron: {},
  }
})
