"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type Profile = {
  name: string; location: string; skills: string[]; languages: string[];
  interests: string[]; career_goals: string; enrollment_status: string;
  field_of_study: string; completeness_score: number;
  education: { institution: string; degree: string; field: string; gpa: number | null }[];
  experience: { title: string; org: string; duration: string; type: string }[];
};

function TagInput({ label, tags, onChange }: { label: string; tags: string[]; onChange: (t: string[]) => void }) {
  const [input, setInput] = useState("");
  const add = () => {
    const trimmed = input.trim();
    if (trimmed && !tags.includes(trimmed)) onChange([...tags, trimmed]);
    setInput("");
  };
  return (
    <div>
      <label style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--color-text-secondary)", textTransform: "uppercase", letterSpacing: "0.04em", display: "block", marginBottom: 8 }}>{label}</label>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 8 }}>
        {tags.map((tag) => (
          <span key={tag} style={{ background: "hsl(258 90% 66% / 0.15)", color: "var(--color-primary-light)", border: "1px solid hsl(258 90% 66% / 0.3)", padding: "3px 10px", borderRadius: "var(--radius-full)", fontSize: "0.8rem", display: "flex", alignItems: "center", gap: 6 }}>
            {tag}
            <button onClick={() => onChange(tags.filter((t) => t !== tag))} style={{ background: "none", border: "none", color: "inherit", cursor: "pointer", opacity: 0.6, fontSize: "1rem", lineHeight: 1, padding: 0 }}>×</button>
          </span>
        ))}
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <input className="input" placeholder={`Add ${label.toLowerCase()}…`} value={input} onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); add(); } }}
          style={{ flex: 1 }} />
        <button className="btn btn-secondary btn-sm" onClick={add}>Add</button>
      </div>
    </div>
  );
}

export default function OnboardingReviewPage() {
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/profile/me`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => r.json())
      .then((data) => { setProfile(data); setLoading(false); });
  }, []);

  async function handleSave() {
    if (!profile) return;
    setSaving(true);
    const token = localStorage.getItem("access_token");
    await fetch(`${process.env.NEXT_PUBLIC_API_URL}/profile/me`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify(profile),
    });
    setSaving(false);
    router.push("/dashboard");
  }

  if (loading || !profile) {
    return (
      <div style={{ minHeight: "100vh", background: "var(--color-bg)", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: "2rem", marginBottom: 16 }}>⏳</div>
          <p style={{ color: "var(--color-text-secondary)" }}>Loading your profile…</p>
        </div>
      </div>
    );
  }

  const completeness = profile.completeness_score || 0;

  return (
    <div style={{ minHeight: "100vh", background: "var(--color-bg)", padding: "40px 24px" }}>
      <div style={{ maxWidth: 680, margin: "0 auto" }}>
        {/* Progress */}
        <div style={{ display: "flex", gap: 8, marginBottom: 48, justifyContent: "center" }}>
          {["Upload", "Review", "Explore"].map((step, i) => (
            <div key={step} style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div style={{ width: 32, height: 32, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", background: i <= 1 ? "var(--color-primary)" : "var(--color-surface-2)", border: i <= 1 ? "none" : "1px solid var(--color-border)", fontSize: "0.8rem", fontWeight: 700, color: i <= 1 ? "white" : "var(--color-text-muted)" }}>{i + 1}</div>
              <span style={{ fontSize: "0.8rem", color: i === 1 ? "var(--color-text)" : "var(--color-text-muted)", fontWeight: i === 1 ? 600 : 400 }}>{step}</span>
              {i < 2 && <div style={{ width: 32, height: 1, background: "var(--color-border)" }} />}
            </div>
          ))}
        </div>

        <h1 style={{ fontSize: "1.8rem", fontWeight: 800, marginBottom: 8 }}>Review your profile</h1>
        <p style={{ color: "var(--color-text-secondary)", marginBottom: 32 }}>We extracted this from your resume. Edit anything that's wrong.</p>

        {/* Completeness bar */}
        <div style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: "var(--radius-lg)", padding: "20px 24px", marginBottom: 28 }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
            <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>Profile completeness</span>
            <span style={{ fontWeight: 800, color: completeness >= 70 ? "var(--color-success)" : "var(--color-primary-light)" }}>{completeness}%</span>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${completeness}%` }} />
          </div>
          {completeness < 60 && (
            <p style={{ fontSize: "0.8rem", color: "var(--color-warning)", marginTop: 10 }}>
              💡 Add more details to unlock better matches
            </p>
          )}
        </div>

        {/* Form */}
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          {/* Basic info */}
          <div className="card" style={{ padding: 24 }}>
            <h2 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: 20 }}>Basic Information</h2>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <div>
                <label style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--color-text-secondary)", textTransform: "uppercase", letterSpacing: "0.04em", display: "block", marginBottom: 8 }}>Full Name</label>
                <input className="input" value={profile.name || ""} onChange={(e) => setProfile({ ...profile, name: e.target.value })} placeholder="Your name" />
              </div>
              <div>
                <label style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--color-text-secondary)", textTransform: "uppercase", letterSpacing: "0.04em", display: "block", marginBottom: 8 }}>Location</label>
                <input className="input" value={profile.location || ""} onChange={(e) => setProfile({ ...profile, location: e.target.value })} placeholder="City, Country" />
              </div>
              <div>
                <label style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--color-text-secondary)", textTransform: "uppercase", letterSpacing: "0.04em", display: "block", marginBottom: 8 }}>Field of Study</label>
                <input className="input" value={profile.field_of_study || ""} onChange={(e) => setProfile({ ...profile, field_of_study: e.target.value })} placeholder="e.g. Computer Science" />
              </div>
              <div>
                <label style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--color-text-secondary)", textTransform: "uppercase", letterSpacing: "0.04em", display: "block", marginBottom: 8 }}>Status</label>
                <select className="input" value={profile.enrollment_status || ""} onChange={(e) => setProfile({ ...profile, enrollment_status: e.target.value })}
                  style={{ background: "var(--color-surface-2)" }}>
                  <option value="">Select status</option>
                  <option value="enrolled">Currently Enrolled</option>
                  <option value="recent_grad">Recent Graduate (≤1 yr)</option>
                  <option value="graduated">Graduated</option>
                </select>
              </div>
            </div>
          </div>

          {/* Skills & interests */}
          <div className="card" style={{ padding: 24 }}>
            <h2 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: 20 }}>Skills & Interests</h2>
            <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
              <TagInput label="Skills" tags={profile.skills || []} onChange={(tags) => setProfile({ ...profile, skills: tags })} />
              <TagInput label="Interests" tags={profile.interests || []} onChange={(tags) => setProfile({ ...profile, interests: tags })} />
              <TagInput label="Languages" tags={profile.languages || []} onChange={(tags) => setProfile({ ...profile, languages: tags })} />
            </div>
          </div>

          {/* Career goals */}
          <div className="card" style={{ padding: 24 }}>
            <h2 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: 20 }}>Career Goals</h2>
            <textarea
              className="input"
              value={profile.career_goals || ""}
              onChange={(e) => setProfile({ ...profile, career_goals: e.target.value })}
              placeholder="Describe your career aspirations and what you're looking for…"
              rows={3}
              style={{ resize: "vertical" }}
            />
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: "flex", gap: 12, marginTop: 32, justifyContent: "flex-end" }}>
          <button className="btn btn-ghost" onClick={() => router.push("/dashboard")}>Skip for now</button>
          <button id="save-profile-btn" className="btn btn-primary btn-lg" onClick={handleSave} disabled={saving}>
            {saving ? "Saving…" : "Save & See My Opportunities →"}
          </button>
        </div>
      </div>
    </div>
  );
}
