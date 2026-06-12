"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/dashboard", label: "Opportunities", icon: "🔭" },
  { href: "/tracker", label: "My Applications", icon: "📋" },
  { href: "/profile", label: "My Profile", icon: "👤" },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      {/* ── Sidebar ──────────────────────────────────────── */}
      <aside className="sidebar">
        {/* Logo */}
        <div style={{ padding: "24px 20px 8px", borderBottom: "1px solid var(--color-border)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: "10px",
                background: "linear-gradient(135deg, var(--color-primary), var(--color-accent))",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "18px",
              }}
            >
              🚀
            </div>
            <div>
              <div style={{ fontWeight: 800, fontSize: "1.05rem", letterSpacing: "-0.02em" }}>
                Zuup
              </div>
              <div style={{ fontSize: "0.7rem", color: "var(--color-text-muted)" }}>
                Opportunity Agent
              </div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav style={{ padding: "16px 12px", flex: 1 }}>
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`sidebar-item ${pathname === item.href ? "active" : ""}`}
            >
              <span style={{ fontSize: "1.1rem" }}>{item.icon}</span>
              {item.label}
            </Link>
          ))}
        </nav>

        {/* Footer */}
        <div
          style={{
            padding: "16px 20px",
            borderTop: "1px solid var(--color-border)",
            fontSize: "0.75rem",
            color: "var(--color-text-muted)",
          }}
        >
          <div>AI-powered discovery</div>
          <div style={{ color: "var(--color-primary-light)", fontWeight: 500, marginTop: 2 }}>
            Agent running ✓
          </div>
        </div>
      </aside>

      {/* ── Main Content ──────────────────────────────────── */}
      <main style={{ flex: 1, overflow: "auto" }}>{children}</main>
    </div>
  );
}
