"use client";

import { useEffect, useState } from "react";
import { Sun, Moon } from "lucide-react";
import { useTheme } from "next-themes";

// Public, farmer-facing chat header. No login/sign-in surfaced here —
// admin/officer auth lives only under /admin (see /login).
export default function ChatHeader({ chatTitle }) {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => { setMounted(true); }, []);

  const toggleTheme = () => setTheme(theme === "dark" ? "light" : "dark");

  const D = {
    header:    "dark:bg-[#21222f] dark:border-[#3a3c52]",
    text:      "dark:text-[#e8eaf0]",
    textMuted: "dark:text-[#9096a8]",
    hover:     "dark:hover:bg-[#2d2f44]",
  };

  return (
    <header className={`h-12 border-b border-gray-200 bg-white flex items-center justify-between px-3 shrink-0 z-10 ${D.header}`}>
      <div className="flex items-center gap-2 min-w-0">
        <span className={`font-semibold text-gray-800 text-sm whitespace-nowrap ${D.text}`}>
          Ganna Sahayak
        </span>
        {chatTitle && chatTitle !== "New Chat" && (
          <>
            <span className="text-gray-300 text-sm hidden sm:inline dark:text-[#3a3c52]">/</span>
            <span className={`text-sm text-gray-500 truncate max-w-[120px] sm:max-w-[200px] hidden sm:block ${D.textMuted}`}>
              {chatTitle}
            </span>
          </>
        )}
      </div>

      {mounted && (
        <button onClick={toggleTheme}
          aria-label={theme === "dark" ? "Light mode" : "Dark mode"}
          className={`p-2 rounded-lg text-gray-500 hover:bg-gray-100 transition ${D.textMuted} ${D.hover}`}>
          {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
        </button>
      )}
    </header>
  );
}
