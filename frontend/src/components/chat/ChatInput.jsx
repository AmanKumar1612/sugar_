"use client";

import { useRef, useState, useEffect } from "react";

export default function ChatInput({ onSend, disabled }) {
  const [text, setText] = useState("");
  const textareaRef = useRef(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 180)}px`;
  }, [text]);

  const send = () => {
    const v = text.trim();
    if (!v || disabled) return;
    onSend(v);
    setText("");
    if (textareaRef.current) textareaRef.current.style.height = "44px";
  };

  useEffect(() => {
    if (typeof window === "undefined") return;
    const h = (e) => { if (e.detail?.text) { setText(e.detail.text); textareaRef.current?.focus(); } };
    window.addEventListener("inject-question", h);
    return () => window.removeEventListener("inject-question", h);
  }, []);

  return (
    <div className="shrink-0 border-t border-gray-200 dark:border-[#3a3c52] bg-white dark:bg-[#21222f] px-4 pt-3 pb-4">
      <div className="max-w-3xl mx-auto flex items-end gap-2.5">
        <textarea
          ref={textareaRef}
          rows={1}
          value={text}
          placeholder="गन्ना योजनाओं के बारे में पूछें / Ask about sugarcane schemes…"
          aria-label="Chat message input"
          disabled={disabled}
          className="
            flex-1 resize-none rounded-xl
            border border-gray-200 dark:border-[#3a3c52]
            bg-gray-50 dark:bg-[#2a2b3d]
            px-4 py-2.5
            text-gray-900 dark:text-[#e8eaf0]
            placeholder-gray-400 dark:placeholder-[#6b7a96]
            text-[15px]
            focus:outline-none focus:border-blue-500 dark:focus:border-blue-500
            focus:ring-2 focus:ring-blue-100 dark:focus:ring-blue-900/40
            focus:bg-white dark:focus:bg-[#2a2b3d]
            transition disabled:opacity-50
          "
          style={{ minHeight: "44px", maxHeight: "180px" }}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
        />
        <button
          onClick={send}
          disabled={!text.trim() || disabled}
          aria-label="Send"
          className="flex items-center justify-center w-10 h-10 rounded-xl bg-blue-600 text-white disabled:opacity-40 disabled:cursor-not-allowed hover:bg-blue-700 transition shrink-0 mb-0.5"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>
      <p className="text-center text-xs text-gray-400 dark:text-[#4a5168] mt-2 select-none">
        Press Enter to send · Shift+Enter for new line
      </p>
    </div>
  );
}
