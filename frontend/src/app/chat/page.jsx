"use client";

import { useState, useEffect, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";

import ChatWindow  from "@/components/chat/ChatWindow";
import ChatInput   from "@/components/chat/ChatInput";
import ChatHeader  from "@/components/chat/ChatHeader";

import { askPublicChat, submitContactInfo, pollQueryStatus } from "@/services/publicChat";

// Public, anonymous farmer-facing chat. No login required — matches the
// backend's /chat/query, /chat/{id}/contact, /chat/{id}/status endpoints.
// Admin/officer login lives only under /admin (see /login), never surfaced here.

const STATUS_POLL_MS = 8000;

export default function ChatPage() {
  return (
    <Suspense fallback={null}>
      <ChatPageInner />
    </Suspense>
  );
}

function ChatPageInner() {
  const searchParams = useSearchParams();
  const [loading,  setLoading]  = useState(false);
  const [messages, setMessages] = useState([]);
  const pollTimers = useRef({});
  const autoSentRef = useRef(false);

  useEffect(() => {
    return () => {
      Object.values(pollTimers.current).forEach(clearInterval);
    };
  }, []);

  const buildHistory = (msgs) =>
    msgs.slice(-6)
      .map((m) => `${m.role === "user" ? "User" : "Assistant"}: ${m.content}`)
      .join("\n");

  const startPolling = (localMsgId, queryId) => {
    pollTimers.current[localMsgId] = setInterval(async () => {
      try {
        const status = await pollQueryStatus(queryId);
        if (status.status === "resolved" && status.officer_reply) {
          clearInterval(pollTimers.current[localMsgId]);
          delete pollTimers.current[localMsgId];
          setMessages((prev) => prev.map((m) =>
            m.id === localMsgId
              ? { ...m, content: status.officer_reply, officerReply: true, awaitingOfficer: false }
              : m
          ));
        }
      } catch {
        // non-fatal — try again on next tick
      }
    }, STATUS_POLL_MS);
  };

  const handleContactSubmit = async (localMsgId, queryId, contact) => {
    try {
      await submitContactInfo(queryId, contact);
      setMessages((prev) => prev.map((m) =>
        m.id === localMsgId ? { ...m, contactCollected: true } : m
      ));
      startPolling(localMsgId, queryId);
    } catch {
      setMessages((prev) => prev.map((m) =>
        m.id === localMsgId ? { ...m, contactError: "Could not save contact info. Please try again." } : m
      ));
    }
  };

  const handleSend = async (userMessage) => {
    const trimmed = userMessage.trim();
    if (!trimmed || loading) return;

    const history = buildHistory(messages);
    setMessages((p) => [...p, { id: crypto.randomUUID(), role: "user", content: trimmed }]);
    setLoading(true);

    try {
      const res = await askPublicChat(trimmed, history);

      if (res.escalated) {
        const assistantId = crypto.randomUUID();
        setMessages((p) => [...p, {
          id: assistantId,
          role: "assistant",
          escalated: true,
          queryId: res.queryId,
          contactRequired: res.contactRequired,
          contactCollected: false,
          awaitingOfficer: true,
          content:
            "मुझे इसका सही जवाब नहीं मिला, इसलिए यह प्रश्न विभाग के अधिकारी को भेज दिया गया है। " +
            "I couldn't find a confident answer, so this has been forwarded to a department officer. " +
            (res.contactRequired ? "Please share your contact details below so they can respond to you." : ""),
        }]);
      } else {
        setMessages((p) => [...p, {
          id: crypto.randomUUID(), role: "assistant",
          content: res.answer, sources: res.sources ?? [],
        }]);
      }
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setMessages((p) => [...p, {
        id: crypto.randomUUID(), role: "assistant",
        content: detail || "Something went wrong. Please try again.", sources: [],
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestion = (text) => {
    window.dispatchEvent(new CustomEvent("inject-question", { detail: { text } }));
  };

  // If the homepage handed off a question via /chat?q=..., send it once on mount.
  useEffect(() => {
    if (autoSentRef.current) return;
    const q = searchParams.get("q");
    if (q && q.trim()) {
      autoSentRef.current = true;
      handleSend(q);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const bottomRef = useRef(null);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-gray-50 dark:bg-[#1e1f2e]">
      <ChatHeader chatTitle="" />
      <ChatWindow
        messages={messages}
        loading={loading}
        bottomRef={bottomRef}
        onSuggestionClick={handleSuggestion}
        onContactSubmit={handleContactSubmit}
      />
      <ChatInput onSend={handleSend} disabled={loading} />
    </div>
  );
}
