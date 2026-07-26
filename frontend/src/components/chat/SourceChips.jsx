"use client";

export default function SourceChips({ sources = [] }) {
  if (!sources.length) return null;

  return (
    <div>
      <p className="text-[11px] font-semibold text-gray-400 dark:text-[#6b7a96] uppercase tracking-widest mb-2">
        Sources
      </p>
      <div className="flex flex-wrap gap-1.5">
        {sources.map((src, i) => {
          const hostname = (() => {
            try { return new URL(src.url).hostname.replace(/^www\./, ""); }
            catch { return ""; }
          })();
          const favicon = hostname
            ? `https://www.google.com/s2/favicons?domain=${hostname}&sz=16`
            : null;

          return (
            <a
              key={i}
              href={src.url}
              target="_blank"
              rel="noopener noreferrer"
              title={src.url}
              className="
                inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg
                border border-gray-200 dark:border-[#3a3c52]
                bg-gray-50 dark:bg-[#2d2f44]
                text-gray-600 dark:text-[#9096a8]
                hover:bg-blue-50 dark:hover:bg-[#2e3356]
                hover:border-blue-300 dark:hover:border-blue-600
                hover:text-blue-700 dark:hover:text-blue-300
                transition max-w-[200px] group
              "
            >
              <span className="flex-shrink-0 w-4 h-4 rounded-full bg-gray-200 dark:bg-[#3a3c52] group-hover:bg-blue-100 dark:group-hover:bg-blue-900/50 flex items-center justify-center text-[10px] font-bold text-gray-500 dark:text-[#9096a8] group-hover:text-blue-600 dark:group-hover:text-blue-400 leading-none">
                {i + 1}
              </span>
              {favicon && (
                <img src={favicon} alt="" aria-hidden="true" className="w-3.5 h-3.5 flex-shrink-0"
                  onError={(e) => { e.currentTarget.style.display = "none"; }} />
              )}
              <span className="truncate font-medium">{src.title || hostname || "Source"}</span>
            </a>
          );
        })}
      </div>
    </div>
  );
}
