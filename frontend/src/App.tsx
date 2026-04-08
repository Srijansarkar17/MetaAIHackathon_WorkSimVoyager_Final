import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import { GameBoard } from './components/game/GameBoard'
import { Playground } from './components/playground/Playground'
import { Gamepad2, Wrench, Home } from 'lucide-react'

function Navigation() {
  const location = useLocation()

  return (
    <nav className="bg-white shadow-sm border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="flex items-center gap-2 text-slate-900 hover:text-blue-600 transition-colors">
              <Home className="h-6 w-6" />
              <span className="font-semibold">WorkSim Voyager</span>
            </Link>
          </div>
          <div className="flex items-center space-x-4">
            <Link
              to="/"
              className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                location.pathname === '/'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <Gamepad2 className="h-4 w-4" />
              Game
            </Link>
            <Link
              to="/playground"
              className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                location.pathname === '/playground'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <Wrench className="h-4 w-4" />
              Playground
            </Link>
          </div>
        </div>
      </div>
    </nav>
  )
}

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-slate-50">
        <Navigation />
        <Routes>
          <Route path="/" element={<GameBoard />} />
          <Route path="/playground" element={<Playground />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
