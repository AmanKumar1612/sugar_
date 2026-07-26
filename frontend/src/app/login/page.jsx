"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { GoogleLogin } from "@react-oauth/google";
import { login, googleLogin } from "@/services/auth";
import useAuthStore from "@/store/authStore";

export default function LoginPage() {
  const router = useRouter();
  const saveLogin = useAuthStore((s) => s.login);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [loading, setLoading] = useState(false);

  const validate = () => {
    const e = {};
    if (!email.trim()) e.email = "Email is required.";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) e.email = "Enter a valid email.";
    if (!password) e.password = "Password is required.";
    return e;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    setErrors(errs);
    setFormError("");
    if (Object.keys(errs).length) return;

    setLoading(true);
    try {
      const res = await login(email, password);
      saveLogin(res.access_token, res.role, res.user);
      router.push("/chat");
    } catch (err) {
      setFormError(err.response?.data?.detail || "Login failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogle = async (credentialResponse) => {
    setFormError("");
    try {
      const res = await googleLogin(credentialResponse.credential);
      saveLogin(res.access_token, res.role, res.user);
      router.push("/chat");
    } catch {
      setFormError("Google sign-in failed. Please try again.");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-7">
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-blue-50 text-blue-600 text-xl mb-3">
            🌾
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Admin & Officer Sign In</h1>
          <p className="text-sm text-gray-500 mt-1">
            For department admins and officers only. Farmers don't need an account —
            just visit the chat directly.
          </p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-8">
          {formError && (
            <div
              role="alert"
              className="mb-5 px-4 py-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-600"
            >
              {formError}
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate>
            {/* Email */}
            <div className="mb-4">
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1.5">
                Email
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (errors.email) setErrors((p) => ({ ...p, email: "" }));
                }}
                className={`w-full px-3.5 py-2.5 rounded-lg border text-gray-900 placeholder-gray-400 text-[15px] focus:outline-none focus:ring-2 focus:ring-blue-100 transition ${
                  errors.email ? "border-red-400 focus:border-red-400" : "border-gray-200 focus:border-blue-500"
                }`}
                placeholder="you@example.com"
                aria-invalid={!!errors.email}
                aria-describedby={errors.email ? "email-error" : undefined}
              />
              {errors.email && (
                <p id="email-error" className="mt-1.5 text-xs text-red-500">{errors.email}</p>
              )}
            </div>

            {/* Password */}
            <div className="mb-5">
              <div className="flex items-center justify-between mb-1.5">
                <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                  Password
                </label>
                <Link href="/forgot-password" className="text-xs text-blue-600 hover:underline">
                  Forgot password?
                </Link>
              </div>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (errors.password) setErrors((p) => ({ ...p, password: "" }));
                }}
                className={`w-full px-3.5 py-2.5 rounded-lg border text-gray-900 placeholder-gray-400 text-[15px] focus:outline-none focus:ring-2 focus:ring-blue-100 transition ${
                  errors.password ? "border-red-400 focus:border-red-400" : "border-gray-200 focus:border-blue-500"
                }`}
                placeholder="••••••••"
                aria-invalid={!!errors.password}
                aria-describedby={errors.password ? "pw-error" : undefined}
              />
              {errors.password && (
                <p id="pw-error" className="mt-1.5 text-xs text-red-500">{errors.password}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg bg-blue-600 text-white font-medium text-[15px] hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed transition flex items-center justify-center gap-2"
            >
              {loading && (
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              )}
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <div className="flex items-center my-5">
            <div className="flex-1 border-t border-gray-100" />
            <span className="px-3 text-xs text-gray-400 font-medium uppercase tracking-wide">or</span>
            <div className="flex-1 border-t border-gray-100" />
          </div>

          <div className="flex justify-center">
            <GoogleLogin
              onSuccess={handleGoogle}
              onError={() => setFormError("Google sign-in failed. Please try again.")}
              size="large"
              shape="rectangular"
              text="signin_with"
              width="100%"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
