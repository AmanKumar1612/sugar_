"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LayoutDashboard, BookOpen, LogOut, Menu, X } from "lucide-react";
import useAuthStore from "@/store/authStore";

const NAV = [
  { href: "/admin/dashboard",    label: "Dashboard",     icon: LayoutDashboard },
  { href: "/admin/knowledge-base", label: "Knowledge Base", icon: BookOpen },
];

export default function AdminLayout({ children }) {
  const pathname = usePathname();
  const router   = useRouter();
  const logout   = useAuthStore((s) => s.logout);
  const token    = useAuthStore((s) => s.token);
  const role     = useAuthStore((s) => s.role);
  const initialize = useAuthStore((s) => s.initialize);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    initialize();
    setReady(true);
  }, [initialize]);

  // Guard: only run after hydration so localStorage is available
  useEffect(() => {
    if (!ready) return;
    if (!token) {
      router.replace("/login");
    } else if (role && role !== "ADMIN" && role !== "SUPER_ADMIN") {
      router.replace("/chat");
    }
  }, [ready, token, role, router]);

  const handleLogout = () => { logout(); router.push("/login"); };

  // Don't flash content while checking auth
  if (!ready || !token) return null;
  if (role && role !== "ADMIN" && role !== "SUPER_ADMIN") return null;

  const Sidebar = ({ mobile = false }) => (
    <aside className={`flex flex-col bg-white border-r border-gray-200 ${mobile ? "w-full h-full" : "w-56 h-screen sticky top-0"}`}>
      <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
        <div>
          <p className="font-semibold text-gray-900 text-[15px]">Ganna Sahayak</p>
          <p className="text-xs text-gray-400">Admin Panel</p>
        </div>
        {mobile && (
          <button onClick={() => setMobileOpen(false)} className="p-1 rounded-lg hover:bg-gray-100"><X size={18} /></button>
        )}
      </div>

      <nav className="flex-1 px-3 py-3 space-y-0.5" aria-label="Admin navigation">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link key={href} href={href} onClick={() => setMobileOpen(false)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition ${active ? "bg-blue-50 text-blue-700 font-medium" : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"}`}
              aria-current={active ? "page" : undefined}>
              <Icon size={16} className={active ? "text-blue-600" : "text-gray-400"} />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="px-3 py-3 border-t border-gray-100">
        <Link href="/chat" className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-500 hover:bg-gray-50 hover:text-gray-800 transition mb-0.5">
          ← Back to Chat
        </Link>
        <button onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-500 hover:bg-red-50 hover:text-red-600 transition">
          <LogOut size={15} /> Sign out
        </button>
      </div>
    </aside>
  );

  return (
    <div className="min-h-screen flex bg-gray-50">
      <div className="hidden md:flex"><Sidebar /></div>

      {mobileOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          <div className="fixed inset-0 bg-black/30" onClick={() => setMobileOpen(false)} />
          <div className="relative w-64 bg-white z-10"><Sidebar mobile /></div>
        </div>
      )}

      <div className="flex-1 flex flex-col min-w-0">
        <div className="md:hidden flex items-center gap-3 px-4 py-3 bg-white border-b border-gray-200">
          <button onClick={() => setMobileOpen(true)}
            className="p-2 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50" aria-label="Open navigation">
            <Menu size={18} />
          </button>
          <p className="font-semibold text-gray-800 text-sm">Ganna Sahayak Admin</p>
        </div>
        <main className="flex-1 p-6 md:p-8 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
