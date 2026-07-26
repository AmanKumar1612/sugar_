"use client";

import { useState } from "react";
import Link from "next/link";
import api from "@/services/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim()) { setError("Please enter your email address."); return; }
    setLoading(true);
    setError("");
    try {
      await api.post("/auth/forgot-password", { email });
      setSubmitted(true);
    } catch {
      // Always show success message to prevent email enumeration
      setSubmitted(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-7">
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-blue-50 text-blue-600 text-xl mb-3">🎓</div>
          <h1 className="text-2xl font-bold text-gray-900">Reset your password</h1>
          <p className="text-sm text-gray-500 mt-1">
            <Link href="/login" className="text-blue-600 hover:underline">← Back to sign in</Link>
          </p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-8">
          {submitted ? (
            <div className="text-center py-4">
              <div className="text-4xl mb-4">📬</div>
              <p className="text-gray-800 font-medium">Check your inbox</p>
              <p className="text-sm text-gray-500 mt-2">
                If that email is registered, we've sent a password reset link. Check your spam folder too.
              </p>
              <Link href="/login"
                className="mt-5 inline-block text-sm px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                Back to sign in
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} noValidate>
              <p className="text-sm text-gray-600 mb-5">
                Enter the email address for your account and we'll send you a reset link.
              </p>
              <div className="mb-4">
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1.5">Email</label>
                <input
                  id="email" type="email" autoComplete="email"
                  value={email} onChange={(e) => { setEmail(e.target.value); setError(""); }}
                  placeholder="you@example.com"
                  className={`w-full px-3.5 py-2.5 rounded-lg border text-gray-900 placeholder-gray-400 text-[15px] focus:outline-none focus:ring-2 focus:ring-blue-100 transition ${error ? "border-red-400" : "border-gray-200 focus:border-blue-500"}`}
                />
                {error && <p className="mt-1.5 text-xs text-red-500">{error}</p>}
              </div>
              <button type="submit" disabled={loading}
                className="w-full py-2.5 rounded-lg bg-blue-600 text-white font-medium text-[15px] hover:bg-blue-700 disabled:opacity-60 transition flex items-center justify-center gap-2">
                {loading && <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />}
                {loading ? "Sending…" : "Send reset link"}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
