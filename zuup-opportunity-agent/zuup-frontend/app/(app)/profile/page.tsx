"use client";

import { useEffect, useState } from "react";

type Profile = {
  name: string; location: string; skills: string[]; languages: string[];
  interests: string[]; career_goals: string; enrollment_status: string;
  field_of_study: string; gpa: number | null;
  completeness_score: number;
  education: { institution: string; degree: string; field: string; gpa: number | null; start_year: number | null; end_year: number | null }[];
  experience: { title: string; org: string; duration: string; type: string }[];
};

function TagEditor({ tags, onChange }: { tags: string[]; onChange: (t: string[]) => void }) {
  const [input, setInput] = useState("");
  const add = () => {
    const t = input.trim();
    if (t && !tags.includes(t)) onChange([...tags, t]);
    setInput("");
  };
  return (
    <div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 10 }}>
        {tags.map((tag) => (
          <span key={tag} style={{ background: "hsl(258 90% 66% / 0.12)", color: "var(--color-primary-light)", border: "1px solid hsl(258 90% 66% / 0.25)", padding: "4px 12px", borderRadius: "var(--radius-full)", fontSize: "0.82rem", display: "flex", alignItems: "center", gap: 6 }}>
            {tag}
            <button onClick={() => onChange(tags.filter((t) => t !== tag))} style={{ background: "none", border: "none", cursor: "pointer", color: "inherit", opacity: 0.6, fontSize: "1rem", lineHeight: 1, padding: 0 }}>×</button>
          </span>
        ))}
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <input className="input" style={{ flex: 1 }} value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); add(); } }} placeholder="Type and press Enter…" />
        <button className="btn btn-secondary btn-sm" onClick={add}>+ Add</button>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="card" style={{ padding: "24px 28px" }}>
      <h2 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: 20, color: "var(--color-text)" }}>{title}</h2>
      {children}
    </div>
  );
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
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
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  }

  if (loading || !profile) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh", flexDirection: "column", gap: 12 }}>
        <div style={{ fontSize: "2rem" }}>⏳</div>
        <p style={{ color: "var(--color-text-secondary)" }}>Loading profile…</p>
      </div>
    );
  }

  const completeness = profile.completeness_score || 0;
  const completenessColor = completeness >= 80 ? "var(--color-success)" : completeness >= 50 ? "var(--color-primary-light)" : "var(--color-warning)";

  return (
    <div style={{ padding: "32px 40px 80px", maxWidth: 800, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 32 }}>
        <div>
          <h1 style={{ fontSize: "1.8rem", fontWeight: 800, marginBottom: 4 }}>My Profile</h1>
          <p style={{ color: "var(--color-text-secondary)" }}>Your agent uses this to find matches.</p>
        </div>
        <button id="save-profile-btn" className="btn btn-primary" onClick={handleSave} disabled={saving}>
          {saved ? "✓ Saved!" : saving ? "Saving…" : "Save Changes"}
        </button>
      </div>

      {/* Completeness */}
      <div style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: "var(--radius-lg)", padding: "20px 24px", marginBottom: 24, display: "flex", alignItems: "center", gap: 20 }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
            <span style={{ fontWeight: 600 }}>Profile strength</span>
            <span style={{ fontWeight: 800, color: completenessColor }}>{completeness}%</span>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${completeness}%` }} />
          </div>
          {completeness < 60 && (
            <p style={{ fontSize: "0.8rem", color: "var(--color-warning)", marginTop: 8 }}>
              💡 Improve your profile to unlock more matches
            </p>
          )}
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        {/* Basic info */}
        <Section title="Basic Information">
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            {[
              { label: "Full Name", field: "name", placeholder: "Your full name" },
              { label: "Location", field: "location", placeholder: "City, Country" },
              { label: "Field of Study", field: "field_of_study", placeholder: "e.g. Computer Science" },
            ].map(({ label, field, placeholder }) => (
              <div key={field}>
                <label style={{ fontSize: "0.78rem", fontWeight: 600, color: "var(--color-text-secondary)", textTransform: "uppercase", letterSpacing: "0.04em", display: "block", marginBottom: 6 }}>{label}</label>
                <input className="input" placeholder={placeholder} value={(profile as any)[field] || ""}
                  onChange={(e) => setProfile({ ...profile, [field]: e.target.value })} />
              </div>
            ))}
            <div>
              <label style={{ fontSize: "0.78rem", fontWeight: 600, color: "var(--color-text-secondary)", textTransform: "uppercase", letterSpacing: "0.04em", display: "block", marginBottom: 6 }}>Status</label>
              <select className="input" style={{ background: "var(--color-surface-2)" }}
                value={profile.enrollment_status || ""}
                onChange={(e) => setProfile({ ...profile, enrollment_status: e.target.value })}>
                <option value="">Select status</option>
                <option value="enrolled">Currently Enrolled</option>
                <option value="recent_grad">Recent Graduate</option>
                <option value="graduated">Graduated</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize: "0.78rem", fontWeight: 600, color: "var(--color-text-secondary)", textTransform: "uppercase", letterSpacing: "0.04em", display: "block", marginBottom: 6 }}>GPA (optional)</label>
              <input type="number" step="0.01" min="0" max="4.0" className="input" placeholder="e.g. 3.7"
                value={profile.gpa ?? ""}
                onChange={(e) => setProfile({ ...profile, gpa: e.target.value ? Number(e.target.value) : null })} />
            </div>
          </div>
        </Section>

        {/* Skills */}
        <Section title="Skills">
          <TagEditor tags={profile.skills || []} onChange={(tags) => setProfile({ ...profile, skills: tags })} />
        </Section>

        {/* Interests */}
        <Section title="Interests">
          <TagEditor tags={profile.interests || []} onChange={(tags) => setProfile({ ...profile, interests: tags })} />
        </Section>

        {/* Languages */}
        <Section title="Languages">
          <TagEditor tags={profile.languages || []} onChange={(tags) => setProfile({ ...profile, languages: tags })} />
        </Section>

        {/* Career goals */}
        <Section title="Career Goals">
          <textarea className="input" rows={4} placeholder="Describe your career aspirations…"
            value={profile.career_goals || ""}
            onChange={(e) => setProfile({ ...profile, career_goals: e.target.value })}
            style={{ resize: "vertical" }} />
        </Section>

        {/* Education */}
        <Section title="Education">
          {(profile.education || []).map((edu, i) => (
            <div key={i} style={{ background: "var(--color-surface-2)", borderRadius: "var(--radius-md)", padding: "16px", marginBottom: 12 }}>
              <div style={{ fontWeight: 700, marginBottom: 4 }}>{edu.institution}</div>
              <div style={{ color: "var(--color-text-secondary)", fontSize: "0.875rem" }}>
                {edu.degree}{edu.field ? ` · ${edu.field}` : ""}{edu.gpa ? ` · GPA ${edu.gpa}` : ""}
              </div>
              {(edu.start_year || edu.end_year) && (
                <div style={{ color: "var(--color-text-muted)", fontSize: "0.8rem", marginTop: 4 }}>
                  {edu.start_year}–{edu.end_year || "Present"}
                </div>
              )}
            </div>
          ))}
          {(!profile.education || profile.education.length === 0) && (
            <p style={{ color: "var(--color-text-muted)", fontSize: "0.875rem" }}>Upload your resume to auto-populate education history.</p>
          )}
        </Section>

        {/* Experience */}
        <Section title="Experience">
          {(profile.experience || []).map((exp, i) => (
            <div key={i} style={{ background: "var(--color-surface-2)", borderRadius: "var(--radius-md)", padding: "16px", marginBottom: 12 }}>
              <div style={{ fontWeight: 700, marginBottom: 4 }}>{exp.title}</div>
              <div style={{ color: "var(--color-text-secondary)", fontSize: "0.875rem" }}>
                {exp.org}{exp.duration ? ` · ${exp.duration}` : ""}
              </div>
              <span style={{ fontSize: "0.72rem", color: "var(--color-text-muted)", textTransform: "capitalize" }}>{exp.type}</span>
            </div>
          ))}
          {(!profile.experience || profile.experience.length === 0) && (
            <p style={{ color: "var(--color-text-muted)", fontSize: "0.875rem" }}>Upload your resume to auto-populate experience.</p>
          )}
        </Section>
      </div>
    </div>
  );
}
