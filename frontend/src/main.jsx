import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Search from './pages/Search'
import ChurchDetail from './pages/ChurchDetail'
import './index.css'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Search />} />
        <Route path="/church/:id" element={<ChurchDetail />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
