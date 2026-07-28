import { motion } from 'framer-motion';
import { Link, NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Layout({ children }) {
  const { user, logout } = useAuth();

  return (
    <div className="app-shell min-h-screen bg-[radial-gradient(circle_at_top,_#f5fff5,_#f7f7f7_60%)] text-slate-800">
      <header className="sticky top-0 z-20 border-b border-emerald-100/80 bg-white/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <Link to="/" className="flex items-center gap-3 text-lg font-semibold text-emerald-700">
            <span className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-100 text-xl shadow-sm">🌾</span>
            Sugarcane AI
          </Link>
          <nav className="hidden items-center gap-6 md:flex">
            <a href="#features" className="text-sm font-medium text-slate-600 transition hover:text-emerald-700">Features</a>
            <a href="#how-it-works" className="text-sm font-medium text-slate-600 transition hover:text-emerald-700">How It Works</a>
            <a href="#contact" className="text-sm font-medium text-slate-600 transition hover:text-emerald-700">Contact</a>
          </nav>
          <div className="flex items-center gap-3">
            {user ? (
              <>
                <NavLink to="/chat" className="rounded-full border border-emerald-200 bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-700">Open Chat</NavLink>
                <button onClick={logout} className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-emerald-200 hover:text-emerald-700">Logout</button>
              </>
            ) : (
              <>
                <NavLink to="/login" className="rounded-full border border-emerald-200 bg-white px-4 py-2 text-sm font-semibold text-emerald-700 transition hover:border-emerald-300">Login</NavLink>
                <NavLink to="/signup" className="rounded-full bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-700">Signup</NavLink>
              </>
            )}
          </div>
        </div>
      </header>
      <motion.main initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45 }}>
        {children}
      </motion.main>
    </div>
  );
}
