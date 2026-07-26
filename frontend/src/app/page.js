"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

const SUGGESTIONS = [
  "गन्ना किसान पंजीकरण कैसे करें?",
  "Mukhyamantri Ganna Vikas Yojana ke liye kaise apply kare?",
  "गुड़ लाइसेंस के लिए क्या दस्तावेज़ चाहिए?",
  "Nearest sugar mill kaha hai?",
];

export default function HomePage() {
  const router = useRouter();
  const [query, setQuery] = useState("");

  const goToChat = (q) => {
    const question = (q ?? query).trim();
    if (!question) {
      router.push("/chat");
      return;
    }
    router.push(`/chat?q=${encodeURIComponent(question)}`);
  };

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Header — no login/sign-up for the public. Admin access is a separate, unlinked route. */}
      <header className="border-b border-gray-100 bg-white sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 h-14 flex items-center">
          <span className="font-semibold text-gray-900 tracking-tight">Ganna Sahayak</span>
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center px-4 pt-12 pb-12">
        <div className="w-full max-w-2xl">
          <div className="text-center mb-7">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-green-50 text-green-700 text-2xl mb-4">🌾</div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">गन्ना उद्योग विभाग सहायक</h1>
            <p className="text-gray-500 text-base">
              Sugarcane Industries Department, Government of Bihar — ask about registration,
              schemes, gur licenses, cane mechanization, and sugar mills. No sign-in needed.
            </p>
          </div>

          {/* Search */}
          <div className="relative">
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); goToChat(); } }}
              placeholder="गन्ना योजनाओं के बारे में पूछें / Ask about sugarcane schemes…"
              rows={1}
              aria-label="Ask a question"
              className="w-full resize-none rounded-xl border border-gray-200 bg-white px-4 py-3.5 pr-14 text-gray-900 placeholder-gray-400 text-[15px] shadow-sm focus:outline-none focus:border-green-600 focus:ring-2 focus:ring-green-100 transition"
              style={{ minHeight: "52px", maxHeight: "160px", overflow: "hidden" }}
            />
            <button
              onClick={() => goToChat()}
              disabled={!query.trim()}
              aria-label="Ask"
              className="absolute right-2.5 bottom-2.5 w-9 h-9 flex items-center justify-center rounded-lg bg-green-700 text-white disabled:opacity-40 hover:bg-green-800 transition"
            >
              <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" /></svg>
            </button>
          </div>

          {/* Suggestions */}
          <div className="mt-5 flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button key={s} onClick={() => goToChat(s)}
                className="text-sm px-3 py-1.5 rounded-full border border-gray-200 text-gray-600 bg-white hover:bg-gray-50 hover:border-gray-300 transition text-left">
                {s}
              </button>
            ))}
          </div>

          <p className="mt-6 text-xs text-gray-400 text-center">
            <a href="/chat" className="hover:text-green-700 hover:underline transition">
              Open full chat →
            </a>
          </p>
        </div>
      </main>

      <footer className="border-t border-gray-100 py-4 text-center text-xs text-gray-400">
        गन्ना उद्योग विभाग, बिहार सरकार — Sugarcane Industries Department, Govt. of Bihar
      </footer>
    </div>
  );
}
