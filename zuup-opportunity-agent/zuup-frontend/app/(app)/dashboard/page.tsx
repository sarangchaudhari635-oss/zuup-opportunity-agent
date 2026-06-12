"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";

type Opportunity = {
  id: string; title: string; type: string; organization: string;
  description_short: string; deadline: string | null; funding_type: string | null;
  location: string | null; remote_eligible: boolean; url: string;
  match_score: number | null; created_at: string;
};

const TYPE_COLORS: Record<string, string> = {
  scholarship: "#8b5cf6", internship: "#0ea5e9",
  fellowship: "#f59e0b", hackathon: "#f97316", exchange: "#3b82f6",
};

const TYPE_LABELS: Record<string, string> = {
  scholarship: "Scholarship", internship: "Internship",
  fellowship: "Fellowship", hackathon: "Hackathon", exchange: "Exchange",
};

function ScoreRing({ score }: { score: number }) {
  const r = 22; const c = 2 * Math.PI * r;
  const offset = c - (score / 100) * c;
  const color = score >= 70 ? "#10b981" : score >= 50 ? "#8b5cf6" : "#f59e0b";
  return (
    <div className="score-ring" style={{ width: 56, height: 56, flexShrink: 0 }}>
      <svg width="56" height="56" viewBox="0 0 56 56">
        <circle cx="28" cy="28" r={r} fill="none" stroke="hsl(222 14% 22%)" strokeWidth="4" />
        <circle cx="28" cy="28" r={r} fill="none" stroke={color} strokeWidth="4"
          strokeDasharray={c} strokeDashoffset={offset} strokeLinecap="round" style={{ transition: "stroke-dashoffset 0.6s ease" }} />
      </svg>
      <span className="score-text" style={{ fontSize: "0.65rem", fontWeight: 800, color }}>{Math.round(score)}%</span>
    </div>
  );
}

function DeadlineChip({ deadline }: { deadline: string | null }) {
  if (!deadline) return null;
  const d = new Date(deadline); const now = new Date();
  const days = Math.ceil((d.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
  const cls = days <= 3 ? "urgent" : days <= 7 ? "soon" : "ok";
  const label = days <= 0 ? "Closing today" : days === 1 ? "1 day left" : days <= 14 ? `${days} days left` : d.toLocaleDateString("en", { month: "short", day: "numeric" });
  return <span className={`deadline-chip ${cls}`}>⏰ {label}</span>;
}

function OpportunityCard({ opp, onSave }: { opp: Opportunity; onSave: (id: string) => void }) {
  const color = TYPE_COLORS[opp.type] || "#8b5cf6";
  return (
    <div className="card animate-fade-in-up" style={{ padding: "20px 24px", display: "flex", gap: 16 }}>
      {opp.match_score !== null && <ScoreRing score={opp.match_score} />}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8, flexWrap: "wrap" }}>
          <span className={`badge badge-${opp.type}`}>{TYPE_LABELS[opp.type] || opp.type}</span>
          <DeadlineChip deadline={opp.deadline} />
          {opp.remote_eligible && <span style={{ fontSize: "0.72rem", color: "var(--color-text-muted)" }}>🌐 Remote</span>}
          {opp.funding_type === "fully_funded" && <span style={{ fontSize: "0.72rem", color: "var(--color-success)" }}>💰 Fully funded</span>}
        </div>
        <h3 style={{ fontSize: "0.95rem", fontWeight: 700, marginBottom: 4, color: "var(--color-text)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{opp.title}</h3>
        <p style={{ fontSize: "0.82rem", color: "var(--color-text-secondary)", marginBottom: 10 }}>{opp.organization}{opp.location ? ` · ${opp.location}` : ""}</p>
        {opp.description_short && (
          <p style={{ fontSize: "0.82rem", color: "var(--color-text-muted)", marginBottom: 12, display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
            {opp.description_short}
          </p>
        )}
        <div style={{ display: "flex", gap: 8 }}>
          <button id={`save-${opp.id}`} className="btn btn-secondary btn-sm" onClick={() => onSave(opp.id)}>Save</button>
          <Link href={opp.url} target="_blank" rel="noopener noreferrer" className="btn btn-ghost btn-sm" style={{ color: "var(--color-primary-light)" }}>
            View → 
          </Link>
        </div>
      </div>
    </div>
  );
}

function SkeletonCard() {
  return (
    <div style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: "var(--radius-lg)", padding: "20px 24px", display: "flex", gap: 16 }}>
      <div className="skeleton" style={{ width: 56, height: 56, borderRadius: "50%", flexShrink: 0 }} />
      <div style={{ flex: 1 }}>
        <div className="skeleton" style={{ height: 16, width: "40%", marginBottom: 12 }} />
        <div className="skeleton" style={{ height: 18, width: "80%", marginBottom: 8 }} />
        <div className="skeleton" style={{ height: 14, width: "50%", marginBottom: 12 }} />
        <div className="skeleton" style={{ height: 32, width: 160 }} />
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [opps, setOpps] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [total, setTotal] = useState(0);
  const [typeFilter, setTypeFilter] = useState<string[]>([]);
  const [remoteOnly, setRemoteOnly] = useState(false);
  const [minScore, setMinScore] = useState(0);
  const [searchQ, setSearchQ] = useState("");
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
  const loaderRef = useRef<HTMLDivElement>(null);

  const fetchOpps = useCallback(async (p: number, reset = false) => {
    setLoading(true);
    const token = localStorage.getItem("access_token");
    const params = new URLSearchParams({ page: p.toString(), page_size: "20" });
    if (remoteOnly) params.set("remote_only", "true");
    if (minScore > 0) params.set("min_score", minScore.toString());
    if (searchQ) params.set("q", searchQ);
    typeFilter.forEach((t) => params.append("type", t));

    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/opportunities?${params}`, { headers: { Authorization: `Bearer ${token}` } });
    const data = await res.json();
    setOpps((prev) => reset ? data.items : [...prev, ...data.items]);
    setHasNext(data.has_next);
    setTotal(data.total);
    setPage(p);
    setLoading(false);
  }, [remoteOnly, minScore, searchQ, typeFilter]);

  useEffect(() => { fetchOpps(1, true); }, [fetchOpps]);

  // Infinite scroll
  useEffect(() => {
    if (!loaderRef.current) return;
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting && hasNext && !loading) fetchOpps(page + 1);
    }, { threshold: 0.1 });
    observer.observe(loaderRef.current);
    return () => observer.disconnect();
  }, [hasNext, loading, page, fetchOpps]);

  async function handleSave(oppId: string) {
    const token = localStorage.getItem("access_token");
    await fetch(`${process.env.NEXT_PUBLIC_API_URL}/applications`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ opportunity_id: oppId, status: "saved" }),
    });
    setSavedIds((prev) => new Set([...prev, oppId]));
  }

  const types = ["scholarship", "internship", "fellowship", "hackathon", "exchange"];

  return (
    <div style={{ padding: "32px 40px 80px", maxWidth: 900, margin: "0 auto" }}>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: "1.8rem", fontWeight: 800, marginBottom: 4 }}>Opportunities</h1>
        <p style={{ color: "var(--color-text-secondary)" }}>
          {total > 0 ? `${total.toLocaleString()} opportunities matched for you` : "Your agent is searching…"}
        </p>
      </div>

      {/* Filter bar */}
      <div className="glass" style={{ padding: "16px 20px", borderRadius: "var(--radius-lg)", marginBottom: 24, display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center", position: "sticky", top: 16, zIndex: 10 }}>
        {/* Search */}
        <input id="search-input" className="input" placeholder="Search opportunities…" value={searchQ} onChange={(e) => setSearchQ(e.target.value)}
          style={{ flex: "1 1 200px", minWidth: 0 }} />

        {/* Type filters */}
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {types.map((t) => (
            <button key={t} id={`filter-${t}`}
              className={`btn btn-sm ${typeFilter.includes(t) ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setTypeFilter((prev) => prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t])}
              style={{ textTransform: "capitalize", padding: "5px 12px" }}>
              {TYPE_LABELS[t]}
            </button>
          ))}
        </div>

        {/* Remote toggle */}
        <button id="remote-toggle"
          className={`btn btn-sm ${remoteOnly ? "btn-primary" : "btn-secondary"}`}
          onClick={() => setRemoteOnly((v) => !v)}>
          🌐 Remote only
        </button>

        {/* Score filter */}
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: "0.8rem", color: "var(--color-text-secondary)", whiteSpace: "nowrap" }}>Min {minScore}%</span>
          <input type="range" min={0} max={80} step={10} value={minScore} onChange={(e) => setMinScore(Number(e.target.value))}
            style={{ accentColor: "var(--color-primary)", cursor: "pointer" }} />
        </div>
      </div>

      {/* Feed */}
      <div className="card-list" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {opps.map((opp) => (
          <OpportunityCard key={opp.id} opp={opp} onSave={handleSave} />
        ))}

        {loading && Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}

        {!loading && opps.length === 0 && (
          <div style={{ textAlign: "center", padding: "80px 24px" }}>
            <div style={{ fontSize: "3rem", marginBottom: 16 }}>🔭</div>
            <h3 style={{ marginBottom: 8 }}>No opportunities found</h3>
            <p style={{ color: "var(--color-text-secondary)" }}>Try adjusting your filters or updating your profile.</p>
          </div>
        )}

        <div ref={loaderRef} style={{ height: 40 }} />
      </div>
    </div>
  );
}
