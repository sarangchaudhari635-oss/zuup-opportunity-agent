"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Registration failed");
      }
      const { access_token, refresh_token } = await res.json();
      localStorage.setItem("access_token", access_token);
      localStorage.setItem("refresh_token", refresh_token);
      router.push("/onboarding/upload");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--color-bg)", padding: "24px" }}>
      {/* Gradient orbs */}
      <div style={{ position: "fixed", top: "-20%", left: "-10%", width: 600, height: 600, borderRadius: "50%", background: "radial-gradient(circle, hsl(185 85% 55% / 0.1), transparent 70%)", pointerEvents: "none" }} />
      <div style={{ position: "fixed", bottom: "-20%", right: "-10%", width: 500, height: 500, borderRadius: "50%", background: "radial-gradient(circle, hsl(258 90% 66% / 0.08), transparent 70%)", pointerEvents: "none" }} />

      <div className="animate-fade-in-up" style={{ width: "100%", maxWidth: 440 }}>
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <div style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", width: 64, height: 64, borderRadius: 18, background: "linear-gradient(135deg, var(--color-primary), var(--color-accent))", fontSize: 28, marginBottom: 16, boxShadow: "0 8px 32px hsl(258 90% 66% / 0.4)" }}>🚀</div>
          <h1 className="gradient-text" style={{ fontSize: "2rem", marginBottom: 8 }}>Join Zuup</h1>
          <p style={{ color: "var(--color-text-secondary)", fontSize: "0.9rem" }}>
            Your AI agent will start finding opportunities immediately.
          </p>
        </div>

        {/* Value props */}
        <div style={{ display: "flex", gap: 12, marginBottom: 28 }}>
          {[
            { icon: "🎯", text: "Personalized matches" },
            { icon: "⚡", text: "Real-time alerts" },
            { icon: "🆓", text: "Always free" },
          ].map((item) => (
            <div key={item.text} style={{ flex: 1, background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: "var(--radius-md)", padding: "10px 8px", textAlign: "center" }}>
              <div style={{ fontSize: "1.1rem", marginBottom: 4 }}>{item.icon}</div>
              <div style={{ fontSize: "0.7rem", color: "var(--color-text-secondary)", fontWeight: 500 }}>{item.text}</div>
            </div>
          ))}
        </div>

        <div className="glass" style={{ padding: "36px", borderRadius: "var(--radius-xl)", boxShadow: "var(--shadow-lg)" }}>
          {error && (
            <div style={{ background: "hsl(4 85% 62% / 0.12)", border: "1px solid hsl(4 85% 62% / 0.3)", color: "var(--color-danger)", padding: "12px 16px", borderRadius: "var(--radius-md)", fontSize: "0.875rem", marginBottom: 20 }}>
              {error}
            </div>
          )}

          <form onSubmit={handleRegister} style={{ display: "flex", flexDirection: "column", gap: 18 }}>
            <div>
              <label htmlFor="reg-email" style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "var(--color-text-secondary)", marginBottom: 8, letterSpacing: "0.04em", textTransform: "uppercase" }}>Email</label>
              <input id="reg-email" type="email" className="input" placeholder="you@university.edu" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
            </div>
            <div>
              <label htmlFor="reg-password" style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "var(--color-text-secondary)", marginBottom: 8, letterSpacing: "0.04em", textTransform: "uppercase" }}>Password</label>
              <input id="reg-password" type="password" className="input" placeholder="Min 8 characters" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} autoComplete="new-password" />
            </div>
            <button id="register-btn" type="submit" className="btn btn-primary btn-lg" disabled={loading} style={{ marginTop: 8 }}>
              {loading ? "Creating account…" : "Create Free Account →"}
            </button>
          </form>

          <p style={{ fontSize: "0.72rem", color: "var(--color-text-muted)", textAlign: "center", marginTop: 16 }}>
            By registering you agree to our{" "}
            <Link href="/terms" style={{ color: "var(--color-text-secondary)" }}>Terms</Link> and{" "}
            <Link href="/privacy" style={{ color: "var(--color-text-secondary)" }}>Privacy Policy</Link>.
          </p>
        </div>

        <p style={{ textAlign: "center", marginTop: 24, color: "var(--color-text-muted)", fontSize: "0.875rem" }}>
          Already have an account?{" "}
          <Link href="/login" style={{ color: "var(--color-primary-light)", fontWeight: 600, textDecoration: "none" }}>Sign in</Link>
        </p>
      </div>
    </div>
  );
}
