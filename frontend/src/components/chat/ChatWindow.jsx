import Message from "./Message";
import TypingIndicator from "./TypingIndicator";
import EmptyState from "./EmptyState";

export default function ChatWindow({ messages, loading, bottomRef, onSuggestionClick, onContactSubmit }) {
  const isEmpty = messages.length === 0 && !loading;

  return (
    <div
      className="flex-1 min-h-0 overflow-y-auto bg-gray-50 dark:bg-[#1e1f2e]"
      aria-live="polite"
      aria-label="Chat messages"
    >
      {isEmpty ? (
        <EmptyState onSuggestionClick={onSuggestionClick} />
      ) : (
        <div className="max-w-3xl mx-auto px-4 py-6 space-y-5">
          {messages.map((msg) => (
            <Message key={msg.id} message={msg} onContactSubmit={onContactSubmit} />
          ))}
          {loading && <TypingIndicator />}
          <div ref={bottomRef} className="h-2" />
        </div>
      )}
    </div>
  );
}
