import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '@arco-design/web-react/dist/css/arco.css'
import '../static/css/style.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
