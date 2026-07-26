import { create } from "zustand";

const useAuthStore = create((set) => ({
  token: null,
  role: null,
  user: null, // { id, name, email, profile_image, provider, is_verified, role }

  /** Rehydrate from localStorage on client mount. Call once in layout or page. */
  initialize: () => {
    if (typeof window === "undefined") return;
    const token = localStorage.getItem("token");
    const role = localStorage.getItem("role");
    const raw = localStorage.getItem("user");
    const user = raw ? JSON.parse(raw) : null;
    set({ token, role, user });
  },

  /** Called after a successful login / register / Google sign-in. */
  login: (token, role, user) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("token", token);
      localStorage.setItem("role", role);
      if (user) localStorage.setItem("user", JSON.stringify(user));
    }
    set({ token, role, user: user ?? null });
  },

  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("token");
      localStorage.removeItem("role");
      localStorage.removeItem("user");
    }
    set({ token: null, role: null, user: null });
  },
}));

export default useAuthStore;
