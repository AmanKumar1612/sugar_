import api from "./api";

const SESSION_KEY = "sugarcane_chat_session_id";

export function getSessionId() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(SESSION_KEY);
}

function saveSessionId(id) {
  if (typeof window === "undefined" || !id) return;
  localStorage.setItem(SESSION_KEY, id);
}

/**
 * Send a question to the public, anonymous chat endpoint (/chat/query).
 * No login required. Backend decides whether to answer directly or
 * escalate to an officer based on confidence.
 *
 * Returns a normalised shape regardless of whether the backend answered
 * directly or escalated:
 *   { escalated: boolean, answer: string|null, sources: [], queryId: string|null, sessionId }
 */
export const askPublicChat = async (question, history = "") => {
  const res = await api.post("/chat/query", {
    question,
    history,
    session_id: getSessionId() || undefined,
  });
  const data = res.data;
  saveSessionId(data.session_id);

  if (data.escalated) {
    return {
      escalated: true,
      answer: null,
      sources: [],
      queryId: data.query_id,
      sessionId: data.session_id,
      contactRequired: !!data.contact_required,
    };
  }

  return {
    escalated: false,
    answer: data.answer,
    sources: data.sources ?? [],
    queryId: null,
    sessionId: data.session_id,
    contactRequired: false,
  };
};

/** Submit farmer contact info for an escalated query so an officer can respond. */
export const submitContactInfo = async (queryId, contact) => {
  const res = await api.post(`/chat/${queryId}/contact`, contact);
  return res.data;
};

/** Poll to see if an officer has replied yet. status: pending_officer | in_progress | resolved */
export const pollQueryStatus = async (queryId) => {
  const res = await api.get(`/chat/${queryId}/status`);
  return res.data;
};
