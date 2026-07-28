import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';

const features = [
  'Instant answers on irrigation, pests, and fertilization',
  'Knowledge base tailored for sugarcane growers',
  'Simple guidance for government schemes and best practices',
];

const steps = ['Ask a question', 'Retrieve relevant farming guidance', 'Receive actionable advice'];

export default function LandingPage() {
  return (
    <div className="pb-16">
      <section className="mx-auto grid max-w-7xl gap-10 px-4 py-16 sm:px-6 lg:grid-cols-[1.05fr_0.95fr] lg:px-8 lg:py-24">
        <motion.div initial={{ opacity: 0, x: -24 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.45 }} className="space-y-8">
          <div className="inline-flex items-center rounded-full border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-700 shadow-sm">AI-powered support for modern farming</div>
          <div className="space-y-4">
            <h1 className="text-4xl font-semibold leading-tight text-slate-900 sm:text-5xl lg:text-6xl">AI Sugarcane Assistant for smarter, more profitable farming</h1>
            <p className="max-w-2xl text-lg leading-8 text-slate-600">Sugarcane AI helps farmers get fast, practical guidance on crop health, irrigation, disease prevention, and government schemes in a conversational experience.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link to="/signup" className="primary-btn rounded-full bg-emerald-600 px-6 py-3 font-semibold text-white shadow-lg shadow-emerald-200">Get Started</Link>
            <Link to="/login" className="secondary-btn rounded-full border border-emerald-200 bg-white px-6 py-3 font-semibold text-emerald-700 shadow-sm">Farmer Login</Link>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            {['24/7 Advice', 'Local Farming Focus', 'Secure & Private'].map((item) => (
              <div key={item} className="rounded-2xl border border-emerald-100 bg-white/80 p-4 shadow-sm backdrop-blur">
                <p className="text-sm font-semibold text-slate-700">{item}</p>
              </div>
            ))}
          </div>
        </motion.div>
        <motion.div initial={{ opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.45 }} className="hero-card glass-panel rounded-[2rem] p-6">
          <div className="rounded-[1.5rem] bg-gradient-to-br from-emerald-700 via-emerald-600 to-lime-500 p-6 text-white shadow-xl">
            <p className="text-sm uppercase tracking-[0.2em] text-white/80">Live assistant</p>
            <h2 className="mt-3 text-2xl font-semibold">Ask about sugarcane growth, disease prevention, and schemes</h2>
            <div className="mt-6 space-y-3">
              <div className="rounded-2xl bg-white/20 p-3 backdrop-blur">How to increase sugarcane production?</div>
              <div className="rounded-2xl bg-white/20 p-3 backdrop-blur">Best fertilizer for sugarcane?</div>
              <div className="rounded-2xl bg-white/20 p-3 backdrop-blur">How to prevent red rot disease?</div>
            </div>
          </div>
        </motion.div>
      </section>

      <section id="features" className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8 flex items-end justify-between gap-4">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.25em] text-emerald-700">Features</p>
            <h2 className="text-3xl font-semibold text-slate-900">Everything a sugarcane farmer needs in one place</h2>
          </div>
        </div>
        <div className="grid gap-5 md:grid-cols-3">
          {features.map((item) => (
            <motion.div whileHover={{ y: -4, scale: 1.01 }} key={item} className="soft-card rounded-[1.5rem] p-6 shadow-sm">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-100 text-xl">✓</div>
              <p className="text-lg font-medium text-slate-800">{item}</p>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="glass-panel rounded-[2rem] border-emerald-100 bg-gradient-to-br from-emerald-50 to-white p-8 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-[0.25em] text-emerald-700">Why choose AI</p>
          <h2 className="mt-2 text-3xl font-semibold text-slate-900">Built for farm realities, not generic chatbots</h2>
          <p className="mt-4 max-w-3xl text-slate-600">The assistant blends retrieval-based knowledge, modern LLM reasoning, and a crop-specific dataset so farmers receive guidance they can trust and apply.</p>
        </div>
      </section>

      <section id="how-it-works" className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8">
          <p className="text-sm font-semibold uppercase tracking-[0.25em] text-emerald-700">How it works</p>
          <h2 className="text-3xl font-semibold text-slate-900">A simple conversational workflow</h2>
        </div>
        <div className="grid gap-5 md:grid-cols-3">
          {steps.map((step, index) => (
            <div key={step} className="soft-card rounded-[1.5rem] p-6 shadow-sm">
              <div className="mb-3 text-sm font-semibold text-amber-500">0{index + 1}</div>
              <h3 className="text-xl font-semibold text-slate-900">{step}</h3>
            </div>
          ))}
        </div>
      </section>

      <section id="contact" className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="glass-panel rounded-[2rem] p-8 shadow-sm">
          <h2 className="text-3xl font-semibold text-slate-900">Ready to bring AI to your field?</h2>
          <p className="mt-2 text-slate-600">Join the platform for farmers, agronomists, and administrators using intelligent guidance every day.</p>
          <Link to="/signup" className="mt-6 inline-flex rounded-full bg-emerald-600 px-6 py-3 font-semibold text-white shadow-lg shadow-emerald-200">Create Account</Link>
        </div>
      </section>
    </div>
  );
}
