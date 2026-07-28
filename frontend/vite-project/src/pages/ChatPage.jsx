import { useEffect, useMemo, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';

const suggestions = [
  'How to increase sugarcane production?',
  'Best fertilizer for sugarcane?',
  'How to prevent red rot disease?',
  'Best irrigation practices?',
  'Government schemes for sugarcane farmers?',
];

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const { user } = useAuth();
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await api.get('/history', { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } });
        const history = response.data.map((item) => [
          { role: 'user', content: item.question },
          { role: 'assistant', content: item.answer },
        ]).flat();
        setMessages(history);
      } catch (error) {
        console.error(error);
      }
    };
    fetchHistory();
  }, []);

  const sendMessage = async (question) => {
    const trimmed = question.trim();
    if (!trimmed) return;
    setMessages((prev) => [...prev, { role: 'user', content: trimmed }]);
    setLoading(true);
    try {
      const response = await api.post('/chat', { question: trimmed }, { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } });
      setMessages((prev) => [...prev, { role: 'assistant', content: response.data.answer }]);
    } catch (error) {
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Unable to answer right now. Please try again.' }]);
    } finally {
      setLoading(false);
      setInput('');
    }
  };

  const greeting = useMemo(() => (user ? `Hello ${user.email.split('@')[0]}!` : 'Hello!'), [user]);

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-8 sm:px-6 lg:flex-row lg:px-8">
      <aside className="glass-panel w-full rounded-[2rem] p-5 shadow-sm lg:w-80">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[#2E7D32]">Chat</p>
            <h2 className="text-xl font-semibold text-slate-900">Sugarcane AI</h2>
          </div>
          <button className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-700">New Chat</button>
        </div>
        <div className="mt-6 space-y-3">
          {suggestions.map((item) => (
            <button key={item} onClick={() => sendMessage(item)} className="w-full rounded-2xl border border-slate-100 bg-slate-50 px-3 py-3 text-left text-sm text-slate-700 transition hover:border-emerald-200 hover:bg-emerald-50">{item}</button>
          ))}
        </div>
      </aside>
      <section className="glass-panel flex-1 rounded-[2rem]">
        <div className="flex h-[72vh] flex-col">
          <div className="flex-1 overflow-y-auto p-6">
            {messages.length === 0 && !loading && (
              <div className="flex h-full items-center justify-center rounded-[1.5rem] border border-dashed border-[#66BB6A]/30 bg-[#f7fcf7] p-6 text-center text-slate-600">
                <div>
                  <h3 className="text-xl font-semibold text-slate-900">{greeting}</h3>
                  <p className="mt-2">Ask your first question about sugarcane farming, irrigation, disease control, or schemes.</p>
                </div>
              </div>
            )}
            {messages.map((message, index) => (
              <motion.div key={`${message.role}-${index}`} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className={`mb-4 max-w-3xl rounded-[1.25rem] px-4 py-3 ${message.role === 'user' ? 'chat-bubble-user ml-auto' : 'chat-bubble-assistant'}`}>
                {message.content}
              </motion.div>
            ))}
            {loading && <div className="rounded-[1.25rem] bg-[#f7fcf7] px-4 py-3 text-slate-700">Thinking…</div>}
            <div ref={endRef} />
          </div>
          <div className="border-t border-slate-100 p-4">
            <form onSubmit={(event) => { event.preventDefault(); sendMessage(input); }} className="input-shell flex gap-3 rounded-full p-2">
              <input value={input} onChange={(event) => setInput(event.target.value)} placeholder="Ask about sugarcane practices..." className="flex-1 bg-transparent px-3 py-2 outline-none" />
              <button className="rounded-full bg-emerald-600 px-4 py-2 font-semibold text-white shadow-sm transition hover:bg-emerald-700">Send</button>
            </form>
          </div>
        </div>
      </section>
    </div>
  );
}
