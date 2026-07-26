"use client";

import { useState } from "react";
import { Copy, Check } from "lucide-react";
import MarkdownRenderer from "./MarkdownRenderer";
import SourceChips from "./SourceChips";

function ContactForm({ messageId, queryId, onContactSubmit, submitting, setSubmitting }) {
  const [name, setName]   = useState("");
  const [phone, setPhone] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!phone.trim()) return;
    setSubmitting(true);
    await onContactSubmit(messageId, queryId, { name: name.trim() || undefined, phone: phone.trim() });
    setSubmitting(false);
  };

  return (
    <form onSubmit={handleSubmit} className="mt-3 pt-3 border-t border-gray-100 dark:border-[#3a3c52] space-y-2">
      <p className="text-xs text-gray-500 dark:text-[#9096a8]">
        अपना नाम और फ़ोन नंबर दें ताकि अधिकारी आपसे संपर्क कर सकें / Share your name and phone so an officer can reach you:
      </p>
      <div className="flex flex-col sm:flex-row gap-2">
        <input
          type="text" value={name} onChange={(e) => setName(e.target.value)}
          placeholder="Name (optional)"
          className="flex-1 text-sm px-3 py-2 rounded-lg border border-gray-200 dark:border-[#3a3c52] bg-white dark:bg-[#1e1f2e] text-gray-900 dark:text-[#e8eaf0]"
        />
        <input
          type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} required
          placeholder="Phone number"
          className="flex-1 text-sm px-3 py-2 rounded-lg border border-gray-200 dark:border-[#3a3c52] bg-white dark:bg-[#1e1f2e] text-gray-900 dark:text-[#e8eaf0]"
        />
        <button
          type="submit" disabled={submitting}
          className="text-sm px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition disabled:opacity-50"
        >
          {submitting ? "..." : "Submit"}
        </button>
      </div>
    </form>
  );
}

export default function MessageBubble({
  messageId, role, content, sources = [],
  escalated, queryId, contactRequired, contactCollected, contactError,
  awaitingOfficer, officerReply, onContactSubmit,
}) {
  const isUser = role === "user";
  const [copied, setCopied] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch { /* unavailable */ }
  };

  /* ── User message ── right-aligned blue bubble ── */
  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[75%] md:max-w-[65%] px-4 py-3 rounded-2xl rounded-tr-sm bg-blue-600 text-white text-[15px] leading-relaxed break-words">
          {content}
        </div>
      </div>
    );
  }

  /* ── Assistant message ── left-aligned card ── */
  return (
    <div className="flex justify-start">
      <div className="max-w-[88%] md:max-w-[78%] w-full">
        {/* Card */}
        <div className="
          px-5 py-4
          rounded-2xl rounded-tl-sm
          bg-white dark:bg-[#272839]
          border border-gray-200 dark:border-[#3a3c52]
          text-gray-900 dark:text-[#e8eaf0]
          break-words overflow-hidden
          shadow-sm
        ">
          <MarkdownRenderer content={content} />

          {escalated && awaitingOfficer && (
            <div className="mt-3 flex items-center gap-2 text-xs text-amber-600 dark:text-amber-400">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
              {contactCollected
                ? "Waiting for an officer to respond… / अधिकारी के जवाब का इंतज़ार है…"
                : "Awaiting your contact details / आपकी संपर्क जानकारी की प्रतीक्षा है"}
            </div>
          )}

          {officerReply && (
            <p className="mt-2 text-xs text-green-600 dark:text-green-400">
              ✓ Answered by department officer / विभागीय अधिकारी द्वारा उत्तर दिया गया
            </p>
          )}

          {escalated && contactRequired && !contactCollected && onContactSubmit && (
            <ContactForm
              messageId={messageId}
              queryId={queryId}
              onContactSubmit={onContactSubmit}
              submitting={submitting}
              setSubmitting={setSubmitting}
            />
          )}

          {contactError && (
            <p className="mt-2 text-xs text-red-500">{contactError}</p>
          )}

          {/* Sources at bottom */}
          {sources && sources.length > 0 && (
            <div className="mt-4 pt-3 border-t border-gray-100 dark:border-[#3a3c52]">
              <SourceChips sources={sources} />
            </div>
          )}
        </div>

        {/* Copy button below card */}
        {!escalated && (
          <button
            onClick={handleCopy}
            aria-label={copied ? "Copied" : "Copy"}
            className="mt-1.5 ml-1 flex items-center gap-1 text-xs text-gray-400 dark:text-[#6b7a96] hover:text-gray-600 dark:hover:text-[#9096a8] px-2 py-1 rounded-md hover:bg-gray-100 dark:hover:bg-[#2d2f44] transition"
          >
            {copied ? <Check size={12} /> : <Copy size={12} />}
            <span>{copied ? "Copied" : "Copy"}</span>
          </button>
        )}
      </div>
    </div>
  );
}
