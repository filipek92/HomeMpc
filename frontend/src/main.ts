import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { Quasar } from 'quasar'
import quasarLang from 'quasar/lang/cs'

// Import icon libraries
import '@quasar/extras/material-icons/material-icons.css'
import '@quasar/extras/fontawesome-v6/fontawesome-v6.css'

// Import Quasar css
import 'quasar/src/css/index.sass'

// Import custom styles
import './styles/main.scss'

import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(Quasar, {
  plugins: {}, // import Quasar plugins and add here
  lang: quasarLang,
  config: {
    brand: {
      primary: '#3B82F6',
      secondary: '#8B5CF6',
      accent: '#10B981',
      dark: '#1F2937',
      positive: '#10B981',
      negative: '#EF4444',
      info: '#06B6D4',
      warning: '#F59E0B'
    }
  }
})

app.mount('#app')
