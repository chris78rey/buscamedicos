export default defineNuxtConfig({
  srcDir: '.',
  devtools: { enabled: true },
  css: [
    'vuetify/styles',
    '@mdi/font/css/materialdesignicons.css',
  ],
  build: {
    transpile: ['vuetify'],
  },
  modules: ['@pinia/nuxt'],
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000/api/v1',
    },
  },
  vite: {
    ssr: {
      noExternal: ['vuetify'],
    },
  },
})
