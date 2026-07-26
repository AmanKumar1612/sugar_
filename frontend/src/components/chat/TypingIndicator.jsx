export default function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div
        className="flex items-center gap-1.5 px-4 py-3 rounded-xl bg-white dark:bg-[#272839] border border-gray-200 dark:border-[#3a3c52] w-fit shadow-sm"
        aria-label="Assistant is typing"
      >
        <span className="typing-dot" />
        <span className="typing-dot" />
        <span className="typing-dot" />
      </div>
    </div>
  );
}
