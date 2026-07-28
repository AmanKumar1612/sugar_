import { useEffect, useState } from 'react';
import api from '../services/api';

export default function AdminPage() {
  const [items, setItems] = useState([]);
  const [form, setForm] = useState({ title: '', category: '', question: '', answer: '', keywords: '' });

  const fetchItems = async () => {
    const response = await api.get('/knowledge', { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } });
    setItems(response.data);
  };

  useEffect(() => {
    fetchItems();
  }, []);

  const handleSubmit = async (event) => {
    event.preventDefault();
    await api.post('/knowledge', form, { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } });
    setForm({ title: '', category: '', question: '', answer: '', keywords: '' });
    fetchItems();
  };

  const handleDelete = async (id) => {
    await api.delete(`/knowledge/${id}`, { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } });
    fetchItems();
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="glass-panel rounded-[2rem] p-6">
        <h1 className="text-3xl font-semibold text-slate-900">Knowledge Management</h1>
        <p className="mt-2 text-slate-600">Add, edit, and remove sugarcane farming knowledge for the chatbot.</p>
        <form onSubmit={handleSubmit} className="mt-6 grid gap-4 lg:grid-cols-2">
          <input value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} placeholder="Title" className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100" />
          <input value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })} placeholder="Category" className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100" />
          <input value={form.question} onChange={(event) => setForm({ ...form, question: event.target.value })} placeholder="Question" className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100" />
          <input value={form.answer} onChange={(event) => setForm({ ...form, answer: event.target.value })} placeholder="Answer" className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100" />
          <input value={form.keywords} onChange={(event) => setForm({ ...form, keywords: event.target.value })} placeholder="Keywords" className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100 lg:col-span-2" />
          <button className="rounded-full bg-emerald-600 px-5 py-3 font-semibold text-white shadow-lg shadow-emerald-200 transition hover:bg-emerald-700 lg:col-span-2">Add Knowledge</button>
        </form>
        <div className="mt-8 overflow-x-auto">
          <table className="admin-table min-w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-slate-600">
                <th className="py-3 pr-4">Title</th>
                <th className="py-3 pr-4">Category</th>
                <th className="py-3 pr-4">Question</th>
                <th className="py-3 pr-4">Answer</th>
                <th className="py-3 pr-4">Date</th>
                <th className="py-3 pr-4">Action</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className="border-b border-slate-100">
                  <td className="py-3 pr-4">{item.title}</td>
                  <td className="py-3 pr-4">{item.category}</td>
                  <td className="py-3 pr-4">{item.question}</td>
                  <td className="py-3 pr-4">{item.answer}</td>
                  <td className="py-3 pr-4">{item.created_at}</td>
                  <td className="py-3 pr-4"><button onClick={() => handleDelete(item.id)} className="rounded-full border border-red-200 px-3 py-1 text-sm font-semibold text-red-600 transition hover:bg-red-50">Delete</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
