"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Login failed");
      }
      const { access_token, refresh_token } = await res.json();
      localStorage.setItem("access_token", access_token);
      localStorage.setItem("refresh_token", refresh_token);
      router.push("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--color-bg)",
        padding: "24px",
      }}
    >
      {/* Background gradient orbs */}
      <div
        style={{
          position: "fixed",
          top: "-20%",
          right: "-10%",
          width: 600,
          height: 600,
          borderRadius: "50%",
          background: "radial-gradient(circle, hsl(258 90% 66% / 0.12), transparent 70%)",
          pointerEvents: "none",
        }}
      />
      <div
        style={{
          position: "fixed",
          bottom: "-20%",
          left: "-10%",
          width: 500,
          height: 500,
          borderRadius: "50%",
          background: "radial-gradient(circle, hsl(185 85% 55% / 0.08), transparent 70%)",
          pointerEvents: "none",
        }}
      />

      <div className="animate-fade-in-up" style={{ width: "100%", maxWidth: 440 }}>
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              width: 64,
              height: 64,
              borderRadius: 18,
              background: "linear-gradient(135deg, var(--color-primary), var(--color-accent))",
              fontSize: 28,
              marginBottom: 16,
              boxShadow: "0 8px 32px hsl(258 90% 66% / 0.4)",
            }}
          >
            🚀
          </div>
          <h1 className="gradient-text" style={{ fontSize: "2rem", marginBottom: 8 }}>
            Welcome back
          </h1>
          <p style={{ color: "var(--color-text-secondary)", fontSize: "0.9rem" }}>
            Your AI agent is waiting for you.
          </p>
        </div>

        {/* Card */}
        <div
          className="glass"
          style={{
            padding: "36px",
            borderRadius: "var(--radius-xl)",
            boxShadow: "var(--shadow-lg)",
          }}
        >
          {error && (
            <div
              style={{
                background: "hsl(4 85% 62% / 0.12)",
                border: "1px solid hsl(4 85% 62% / 0.3)",
                color: "var(--color-danger)",
                padding: "12px 16px",
                borderRadius: "var(--radius-md)",
                fontSize: "0.875rem",
                marginBottom: 20,
              }}
            >
              {error}
            </div>
          )}

          <form onSubmit={handleLogin} style={{ display: "flex", flexDirection: "column", gap: 18 }}>
            <div>
              <label
                htmlFor="email"
                style={{
                  display: "block",
                  fontSize: "0.8rem",
                  fontWeight: 600,
                  color: "var(--color-text-secondary)",
                  marginBottom: 8,
                  letterSpacing: "0.04em",
                  textTransform: "uppercase",
                }}
              >
                Email
              </label>
              <input
                id="email"
                type="email"
                className="input"
                placeholder="you@university.edu"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>

            <div>
              <label
                htmlFor="password"
                style={{
                  display: "block",
                  fontSize: "0.8rem",
                  fontWeight: 600,
                  color: "var(--color-text-secondary)",
                  marginBottom: 8,
                  letterSpacing: "0.04em",
                  textTransform: "uppercase",
                }}
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                className="input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </div>

            <button
              id="login-btn"
              type="submit"
              className="btn btn-primary btn-lg"
              disabled={loading}
              style={{ marginTop: 8 }}
            >
              {loading ? (
                <span style={{ opacity: 0.8 }}>Signing in…</span>
              ) : (
                "Sign In"
              )}
            </button>
          </form>

          {/* Divider */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              margin: "24px 0",
              color: "var(--color-text-muted)",
              fontSize: "0.8rem",
            }}
          >
            <div style={{ flex: 1, height: 1, background: "var(--color-border)" }} />
            or
            <div style={{ flex: 1, height: 1, background: "var(--color-border)" }} />
          </div>

          {/* Google OAuth */}
          <button
            id="google-login-btn"
            className="btn btn-secondary"
            style={{ width: "100%" }}
            onClick={async () => {
              const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/google`);
              const { auth_url } = await res.json();
              window.location.href = auth_url;
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Continue with Google
          </button>
        </div>

        {/* Sign up link */}
        <p
          style={{
            textAlign: "center",
            marginTop: 24,
            color: "var(--color-text-muted)",
            fontSize: "0.875rem",
          }}
        >
          New to Zuup?{" "}
          <Link
            href="/register"
            style={{ color: "var(--color-primary-light)", fontWeight: 600, textDecoration: "none" }}
          >
            Create your account
          </Link>
        </p>
      </div>
    </div>
  );
}
