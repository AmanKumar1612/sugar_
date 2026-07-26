"use client";

import { useEffect, useState } from "react";
import { getOverview, getTopSearches } from "@/services/analytics";
import { Users, MessageSquare, FileText, Search, AlertCircle } from "lucide-react";

const STAT_CONFIG = [
  { key: "total_users",     label: "Users",      icon: Users,         color: "text-blue-600",  bg: "bg-blue-50" },
  { key: "total_chats",     label: "Chats",      icon: MessageSquare, color: "text-indigo-600", bg: "bg-indigo-50" },
  { key: "total_documents", label: "Documents",  icon: FileText,      color: "text-emerald-600", bg: "bg-emerald-50" },
  { key: "total_searches",  label: "Searches",   icon: Search,        color: "text-amber-600",  bg: "bg-amber-50" },
  { key: "failed_searches", label: "Failed",     icon: AlertCircle,   color: "text-red-500",   bg: "bg-red-50" },
];

function StatCard({ label, value, icon: Icon, color, bg, loading }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm text-gray-500 font-medium">{label}</p>
        <div className={`w-8 h-8 rounded-lg ${bg} flex items-center justify-center`}>
          <Icon size={15} className={color} />
        </div>
      </div>
      <p className="text-3xl font-bold text-gray-900">
        {loading ? <span className="text-gray-200 animate-pulse">—</span> : (value ?? 0).toLocaleString()}
      </p>
    </div>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [searches, setSearches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError("");
    try {
      const [overview, top] = await Promise.all([
        getOverview(),
        getTopSearches(),
      ]);
      setStats(overview);
      setSearches(top ?? []);
    } catch {
      setError("Failed to load analytics. Check that you have admin access.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl">
      <div className="mb-7">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-sm text-gray-500 mt-0.5">Overview of chatbot usage</p>
      </div>

      {error && (
        <div className="mb-6 px-4 py-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-600">
          {error}
        </div>
      )}

      {/* Stats grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
        {STAT_CONFIG.map(({ key, label, icon, color, bg }) => (
          <StatCard
            key={key}
            label={label}
            value={stats?.[key]}
            icon={icon}
            color={color}
            bg={bg}
            loading={loading}
          />
        ))}
      </div>

      {/* Top searches */}
      <div className="bg-white border border-gray-200 rounded-xl">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900 text-[15px]">Top Searches</h2>
          <p className="text-xs text-gray-400 mt-0.5">Most frequent queries across all users</p>
        </div>

        {loading ? (
          <div className="px-5 py-8 text-center text-sm text-gray-400">Loading…</div>
        ) : searches.length === 0 ? (
          <div className="px-5 py-8 text-center text-sm text-gray-400">No search data yet.</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="px-5 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">#</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">Query</th>
                <th className="px-5 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wide">Count</th>
              </tr>
            </thead>
            <tbody>
              {searches.map((item, i) => (
                <tr key={item.query} className="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition">
                  <td className="px-5 py-3 text-gray-400 tabular-nums">{i + 1}</td>
                  <td className="px-5 py-3 text-gray-700 max-w-xs truncate">{item.query}</td>
                  <td className="px-5 py-3 text-right font-medium text-gray-900 tabular-nums">{item.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
