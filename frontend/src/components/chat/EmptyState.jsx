const SUGGESTIONS = [
  "गन्ना किसान पंजीकरण कैसे करें?",
  "Mukhyamantri Ganna Vikas Yojana ke liye kaise apply kare?",
  "गुड़ लाइसेंस के लिए क्या दस्तावेज़ चाहिए?",
  "What is the gur license application process?",
  "गन्ना यंत्रीकरण योजना में सब्सिडी कितनी मिलती है?",
  "Nearest sugar mill kaha hai?",
];

export default function EmptyState({ onSuggestionClick }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-full px-6 py-14 text-center">
      <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-blue-50 dark:bg-blue-900/25 text-2xl mb-4">
        🌾
      </div>
      <h2 className="text-xl font-semibold text-gray-900 dark:text-[#e8eaf0] mb-2">
        How can I help you today?
      </h2>
      <p className="text-sm text-gray-500 dark:text-[#9096a8] max-w-sm mb-8">
        गन्ना पंजीकरण, विभागीय योजनाओं, गुड़ लाइसेंस, या चीनी मिलों के बारे में पूछें।
        Ask about cane registration, department schemes, gur licenses, or sugar mills —
        in Hindi, Hinglish, or English.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-xl">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => onSuggestionClick?.(s)}
            className="
              text-left text-sm px-4 py-3 rounded-xl
              border border-gray-200 dark:border-[#3a3c52]
              bg-white dark:bg-[#272839]
              text-gray-700 dark:text-[#c8ccda]
              hover:bg-blue-50 dark:hover:bg-[#2d2f44]
              hover:border-blue-200 dark:hover:border-blue-700
              hover:text-blue-700 dark:hover:text-blue-300
              transition leading-snug
            "
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
