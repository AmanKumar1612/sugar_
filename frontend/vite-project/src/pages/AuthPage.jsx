import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';

export default function AuthPage({ mode = 'login' }) {
  const [form, setForm] = useState({
    email: '',
    password: '',
    confirm_password: '',
    full_name: '',
    phone: '',
    village: '',
    district: '',
    state: '',
    role: 'farmer',
    admin_secret_key: '',
  });
  const [error, setError] = useState('');
  const { login, signup } = useAuth();
  const navigate = useNavigate();

  const handleChange = (event) => {
    setForm({ ...form, [event.target.name]: event.target.value });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    try {
      if (mode === 'login') {
        await login({ email: form.email, password: form.password, remember_me: true });
      } else {
        await signup({ ...form, role: form.role, admin_secret_key: form.admin_secret_key });
      }
      navigate('/chat');
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication failed');
    }
  };

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-16 sm:px-6 lg:flex-row lg:px-8">
      <motion.div initial={{ opacity: 0, x: -24 }} animate={{ opacity: 1, x: 0 }} className="glass-panel flex-1 rounded-[2rem] p-8 shadow-sm">
        <h1 className="text-3xl font-semibold text-slate-900">{mode === 'login' ? 'Farmer Login' : 'Create Farmer or Admin Account'}</h1>
        <p className="mt-3 text-slate-600">Secure sign-in with JWT support, Google-ready flow, and role-aware access.</p>
        {error && <div className="mt-4 rounded-2xl bg-red-50 p-3 text-sm text-red-600">{error}</div>}
        <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
          {mode !== 'login' && (
            <>
              <input name="full_name" value={form.full_name} onChange={handleChange} placeholder="Full Name" className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100" />
              <input name="phone" value={form.phone} onChange={handleChange} placeholder="Phone" className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100" />
              <div className="grid gap-4 sm:grid-cols-2">
                <input name="village" value={form.village} onChange={handleChange} placeholder="Village" className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100" />
                <input name="district" value={form.district} onChange={handleChange} placeholder="District" className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100" />
              </div>
              <input name="state" value={form.state} onChange={handleChange} placeholder="State" className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100" />
              <select name="role" value={form.role} onChange={handleChange} className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100">
                <option value="farmer">Farmer</option>
                <option value="admin">Admin</option>
              </select>
              {form.role === 'admin' && <input name="admin_secret_key" value={form.admin_secret_key} onChange={handleChange} placeholder="Admin Secret Key" className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100" />}
            </>
          )}
          {mode === 'login' && (
            <>
              <input type="email" name="email" value={form.email} onChange={handleChange} placeholder="Email" className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none" />
              <input type="password" name="password" value={form.password} onChange={handleChange} placeholder="Password" className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none" />
            </>
          )}
          {mode !== 'login' && (
            <>
              <input type="email" name="email" value={form.email} onChange={handleChange} placeholder="Email" className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100" />
              <input type="password" name="password" value={form.password} onChange={handleChange} placeholder="Password" className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100" />
              <input type="password" name="confirm_password" value={form.confirm_password} onChange={handleChange} placeholder="Confirm Password" className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100" />
            </>
          )}
          <button className="w-full rounded-full bg-emerald-600 px-4 py-3 font-semibold text-white shadow-lg shadow-emerald-200 transition hover:bg-emerald-700">{mode === 'login' ? 'Login' : 'Create Account'}</button>
        </form>
      </motion.div>
      <motion.div initial={{ opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }} className="hero-card flex-1 rounded-[2rem] border border-[#66BB6A]/20 bg-gradient-to-br from-[#2E7D32] to-[#66BB6A] p-8 text-white shadow-lg">
        <h2 className="text-2xl font-semibold">Secure access for every farmer</h2>
        <p className="mt-3 text-white/80">Use strong credentials, role-based access, and built-in token refresh to keep your farm assistant secure.</p>
        <div className="mt-6 space-y-3">
          <div className="rounded-2xl bg-white/20 p-4">Google-ready OAuth path</div>
          <div className="rounded-2xl bg-white/20 p-4">Forgot password experience</div>
          <div className="rounded-2xl bg-white/20 p-4">Farmer and admin roles</div>
        </div>
      </motion.div>
    </div>
  );
}
