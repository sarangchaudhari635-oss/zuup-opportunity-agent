"use client";

import { useEffect, useState } from "react";

type Application = {
  id: string; status: string; notes: string | null;
  opportunity: { id: string; title: string; type: string; organization: string; deadline: string | null; url: string; };
  updated_at: string;
};

const COLUMNS = [
  { key: "saved", label: "Saved", icon: "🔖" },
  { key: "applied", label: "Applied", icon: "📤" },
  { key: "under_review", label: "Under Review", icon: "👀" },
  { key: "shortlisted", label: "Shortlisted", icon: "⭐" },
  { key: "outcome", label: "Outcome", icon: "🏆" },
];

const TYPE_COLORS: Record<string, string> = {
  scholarship: "#8b5cf6", internship: "#0ea5e9",
  fellowship: "#f59e0b", hackathon: "#f97316", exchange: "#3b82f6",
};

function DeadlineBadge({ deadline }: { deadline: string | null }) {
  if (!deadline) return null;
  const d = new Date(deadline); const now = new Date();
  const days = Math.ceil((d.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
  if (days < 0) return <span style={{ fontSize: "0.72rem", color: "var(--color-danger)" }}>Closed</span>;
  const cls = days <= 7 ? "urgent" : "ok";
  return <span className={`deadline-chip ${cls}`}>⏰ {days}d left</span>;
}

export default function TrackerPage() {
  const [apps, setApps] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedApp, setSelectedApp] = useState<Application | null>(null);
  const [notes, setNotes] = useState("");
  const [savingNotes, setSavingNotes] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/applications`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => r.json())
      .then((data) => { setApps(Array.isArray(data) ? data : []); setLoading(false); });
  }, []);

  async function moveToStatus(appId: string, newStatus: string) {
    const token = localStorage.getItem("access_token");
    await fetch(`${process.env.NEXT_PUBLIC_API_URL}/applications/${appId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ status: newStatus }),
    });
    setApps((prev) => prev.map((a) => a.id === appId ? { ...a, status: newStatus } : a));
  }

  async function saveNotes() {
    if (!selectedApp) return;
    setSavingNotes(true);
    const token = localStorage.getItem("access_token");
    await fetch(`${process.env.NEXT_PUBLIC_API_URL}/applications/${selectedApp.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ notes }),
    });
    setApps((prev) => prev.map((a) => a.id === selectedApp.id ? { ...a, notes } : a));
    setSavingNotes(false);
  }

  async function exportCSV() {
    const token = localStorage.getItem("access_token");
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/applications/export/csv`, { headers: { Authorization: `Bearer ${token}` } });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = "zuup_applications.csv"; a.click();
  }

  const grouped = COLUMNS.reduce((acc, col) => {
    acc[col.key] = apps.filter((a) => a.status === col.key);
    return acc;
  }, {} as Record<string, Application[]>);

  return (
    <div style={{ padding: "32px 40px 80px" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 32 }}>
        <div>
          <h1 style={{ fontSize: "1.8rem", fontWeight: 800, marginBottom: 4 }}>My Applications</h1>
          <p style={{ color: "var(--color-text-secondary)" }}>{apps.length} tracked · Drag cards to update status</p>
        </div>
        <button id="export-csv-btn" className="btn btn-secondary btn-sm" onClick={exportCSV}>↓ Export CSV</button>
      </div>

      {loading ? (
        <div style={{ textAlign: "center", padding: 80 }}>
          <div style={{ fontSize: "2rem", marginBottom: 12 }}>⏳</div>
          <p style={{ color: "var(--color-text-secondary)" }}>Loading your tracker…</p>
        </div>
      ) : apps.length === 0 ? (
        <div style={{ textAlign: "center", padding: 80 }}>
          <div style={{ fontSize: "3.5rem", marginBottom: 16 }}>📋</div>
          <h3 style={{ marginBottom: 8 }}>No applications yet</h3>
          <p style={{ color: "var(--color-text-secondary)", marginBottom: 24 }}>Save opportunities from your feed to start tracking.</p>
          <a href="/dashboard" className="btn btn-primary">Browse Opportunities →</a>
        </div>
      ) : (
        <div style={{ display: "flex", gap: 16, overflowX: "auto", paddingBottom: 16 }}>
          {COLUMNS.map((col) => (
            <div key={col.key} style={{ minWidth: 280, flex: "0 0 280px" }}>
              {/* Column header */}
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12, padding: "8px 12px", background: "var(--color-surface)", borderRadius: "var(--radius-md)", border: "1px solid var(--color-border)" }}>
                <span>{col.icon}</span>
                <span style={{ fontWeight: 700, fontSize: "0.875rem" }}>{col.label}</span>
                <span style={{ marginLeft: "auto", background: "var(--color-surface-2)", borderRadius: "var(--radius-full)", padding: "1px 8px", fontSize: "0.75rem", color: "var(--color-text-muted)" }}>
                  {grouped[col.key]?.length || 0}
                </span>
              </div>

              {/* Cards */}
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {(grouped[col.key] || []).map((app) => {
                  const typeColor = TYPE_COLORS[app.opportunity.type] || "#8b5cf6";
                  return (
                    <div key={app.id} id={`app-card-${app.id}`}
                      className="card"
                      style={{ padding: 16, cursor: "pointer" }}
                      onClick={() => { setSelectedApp(app); setNotes(app.notes || ""); }}>
                      <div style={{ display: "flex", gap: 6, marginBottom: 8 }}>
                        <span style={{ fontSize: "0.7rem", fontWeight: 700, background: `${typeColor}20`, color: typeColor, padding: "2px 8px", borderRadius: "var(--radius-full)", textTransform: "capitalize" }}>
                          {app.opportunity.type}
                        </span>
                        <DeadlineBadge deadline={app.opportunity.deadline} />
                      </div>
                      <p style={{ fontSize: "0.875rem", fontWeight: 600, marginBottom: 4, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {app.opportunity.title}
                      </p>
                      <p style={{ fontSize: "0.78rem", color: "var(--color-text-muted)" }}>{app.opportunity.organization}</p>

                      {/* Quick move buttons */}
                      <div style={{ display: "flex", gap: 4, marginTop: 12, flexWrap: "wrap" }}>
                        {COLUMNS.filter((c) => c.key !== col.key).map((c) => (
                          <button key={c.key} id={`move-${app.id}-${c.key}`}
                            className="btn btn-ghost btn-sm"
                            style={{ fontSize: "0.68rem", padding: "3px 8px" }}
                            onClick={(e) => { e.stopPropagation(); moveToStatus(app.id, c.key); }}>
                            → {c.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Side panel */}
      {selectedApp && (
        <div style={{
          position: "fixed", inset: 0, zIndex: 50,
          display: "flex", justifyContent: "flex-end",
        }}>
          <div style={{ position: "absolute", inset: 0, background: "hsl(0 0% 0% / 0.5)" }} onClick={() => setSelectedApp(null)} />
          <div style={{ position: "relative", width: 420, background: "var(--color-surface)", borderLeft: "1px solid var(--color-border)", padding: 32, overflowY: "auto", zIndex: 1 }}>
            <button onClick={() => setSelectedApp(null)} className="btn btn-ghost btn-sm" style={{ marginBottom: 24 }}>← Back</button>
            <h2 style={{ fontSize: "1.1rem", fontWeight: 800, marginBottom: 4 }}>{selectedApp.opportunity.title}</h2>
            <p style={{ color: "var(--color-text-secondary)", marginBottom: 24 }}>{selectedApp.opportunity.organization}</p>
            <DeadlineBadge deadline={selectedApp.opportunity.deadline} />
            <div style={{ marginTop: 24 }}>
              <label style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--color-text-secondary)", textTransform: "uppercase", letterSpacing: "0.04em", display: "block", marginBottom: 8 }}>Notes</label>
              <textarea className="input" value={notes} onChange={(e) => setNotes(e.target.value)} rows={5} placeholder="Add notes about this application…" style={{ resize: "vertical" }} />
              <button className="btn btn-primary" style={{ marginTop: 12 }} onClick={saveNotes} disabled={savingNotes}>
                {savingNotes ? "Saving…" : "Save Notes"}
              </button>
            </div>
            <div style={{ marginTop: 24 }}>
              <a href={selectedApp.opportunity.url} target="_blank" rel="noopener noreferrer" className="btn btn-secondary" style={{ width: "100%", justifyContent: "center" }}>
                Open Application →
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
