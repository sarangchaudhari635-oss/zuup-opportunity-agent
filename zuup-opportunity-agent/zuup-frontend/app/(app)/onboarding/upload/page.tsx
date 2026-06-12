"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";

const PROCESSING_STEPS = [
  "Reading your resume…",
  "Extracting skills & experience…",
  "Analyzing education history…",
  "Building your opportunity profile…",
  "Almost ready…",
];

export default function OnboardingUploadPage() {
  const router = useRouter();
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);
  const [error, setError] = useState("");
  const [jobId, setJobId] = useState("");

  const handleFile = useCallback((f: File) => {
    if (!["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"].includes(f.type)) {
      setError("Only PDF or DOCX files are supported.");
      return;
    }
    if (f.size > 10 * 1024 * 1024) {
      setError("File must be under 10MB.");
      return;
    }
    setError("");
    setFile(f);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) handleFile(dropped);
  }, [handleFile]);

  async function handleUpload() {
    if (!file) return;
    setUploading(true);
    setError("");

    const token = localStorage.getItem("access_token");
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/resume/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      if (!res.ok) throw new Error("Upload failed. Please try again.");
      const { job_id } = await res.json();
      setJobId(job_id);
      setUploading(false);
      setProcessing(true);

      // Animate processing steps
      let step = 0;
      const interval = setInterval(() => {
        step = Math.min(step + 1, PROCESSING_STEPS.length - 1);
        setStepIndex(step);
      }, 5000);

      // Poll for completion
      const poll = async () => {
        const statusRes = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/resume/status/${job_id}`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        const status = await statusRes.json();
        if (status.status === "done") {
          clearInterval(interval);
          router.push("/onboarding/review");
        } else if (status.status === "failed") {
          clearInterval(interval);
          setProcessing(false);
          setError("Resume parsing failed. Please try again or fill your profile manually.");
        } else {
          setTimeout(poll, 3000);
        }
      };
      setTimeout(poll, 3000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Upload failed");
      setUploading(false);
      setProcessing(false);
    }
  }

  return (
    <div style={{ minHeight: "100vh", background: "var(--color-bg)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "24px" }}>
      {/* Progress indicator */}
      <div style={{ display: "flex", gap: 8, marginBottom: 48 }}>
        {["Upload", "Review", "Explore"].map((step, i) => (
          <div key={step} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{
              width: 32, height: 32, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center",
              background: i === 0 ? "var(--color-primary)" : "var(--color-surface-2)",
              border: i === 0 ? "none" : "1px solid var(--color-border)",
              fontSize: "0.8rem", fontWeight: 700, color: i === 0 ? "white" : "var(--color-text-muted)"
            }}>{i + 1}</div>
            <span style={{ fontSize: "0.8rem", color: i === 0 ? "var(--color-text)" : "var(--color-text-muted)", fontWeight: i === 0 ? 600 : 400 }}>{step}</span>
            {i < 2 && <div style={{ width: 32, height: 1, background: "var(--color-border)" }} />}
          </div>
        ))}
      </div>

      <div style={{ width: "100%", maxWidth: 560, textAlign: "center" }}>
        <h1 style={{ fontSize: "2rem", fontWeight: 800, marginBottom: 8 }}>
          {processing ? "Analyzing your resume" : "Upload your resume"}
        </h1>
        <p style={{ color: "var(--color-text-secondary)", marginBottom: 40 }}>
          {processing ? "Your AI agent is building your opportunity profile." : "We'll extract your profile automatically — no form filling."}
        </p>

        {/* Processing state */}
        {processing ? (
          <div className="glass" style={{ padding: 48, borderRadius: "var(--radius-xl)" }}>
            {/* Spinner */}
            <div style={{ position: "relative", width: 80, height: 80, margin: "0 auto 24px" }}>
              <svg width="80" height="80" style={{ animation: "spin 1.5s linear infinite" }}>
                <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
                <circle cx="40" cy="40" r="34" fill="none" stroke="var(--color-surface-3)" strokeWidth="4" />
                <circle cx="40" cy="40" r="34" fill="none" stroke="var(--color-primary)" strokeWidth="4"
                  strokeDasharray="160" strokeDashoffset="100" strokeLinecap="round" />
              </svg>
              <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.8rem" }}>🤖</div>
            </div>
            <p style={{ color: "var(--color-primary-light)", fontWeight: 600, marginBottom: 8 }}>
              {PROCESSING_STEPS[stepIndex]}
            </p>
            <p style={{ color: "var(--color-text-muted)", fontSize: "0.85rem" }}>This usually takes under 30 seconds.</p>
          </div>
        ) : (
          <>
            {/* Drop zone */}
            <div
              id="resume-dropzone"
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              onClick={() => document.getElementById("file-input")?.click()}
              style={{
                border: `2px dashed ${isDragging ? "var(--color-primary)" : file ? "var(--color-success)" : "var(--color-border)"}`,
                borderRadius: "var(--radius-xl)",
                padding: "56px 32px",
                cursor: "pointer",
                transition: "all 0.2s ease",
                background: isDragging ? "hsl(258 90% 66% / 0.06)" : file ? "hsl(145 65% 50% / 0.04)" : "var(--color-surface)",
                marginBottom: 24,
              }}
            >
              <input id="file-input" type="file" accept=".pdf,.docx" style={{ display: "none" }} onChange={(e) => { if (e.target.files?.[0]) handleFile(e.target.files[0]); }} />
              <div style={{ fontSize: "3rem", marginBottom: 16 }}>{file ? "✅" : "📄"}</div>
              {file ? (
                <>
                  <p style={{ fontWeight: 700, fontSize: "1rem", marginBottom: 4 }}>{file.name}</p>
                  <p style={{ color: "var(--color-text-muted)", fontSize: "0.85rem" }}>{(file.size / 1024).toFixed(0)} KB — Click to change</p>
                </>
              ) : (
                <>
                  <p style={{ fontWeight: 600, fontSize: "1rem", marginBottom: 8 }}>Drop your resume here</p>
                  <p style={{ color: "var(--color-text-muted)", fontSize: "0.85rem" }}>PDF or DOCX, up to 10MB</p>
                  <div style={{ marginTop: 16 }}>
                    <span className="btn btn-secondary btn-sm" style={{ pointerEvents: "none" }}>Browse file</span>
                  </div>
                </>
              )}
            </div>

            {error && (
              <div style={{ background: "hsl(4 85% 62% / 0.12)", border: "1px solid hsl(4 85% 62% / 0.3)", color: "var(--color-danger)", padding: "12px 16px", borderRadius: "var(--radius-md)", marginBottom: 16, fontSize: "0.875rem" }}>
                {error}
              </div>
            )}

            <div style={{ display: "flex", gap: 12, justifyContent: "center" }}>
              <button
                id="upload-resume-btn"
                className="btn btn-primary btn-lg"
                onClick={handleUpload}
                disabled={!file || uploading}
                style={{ minWidth: 200 }}
              >
                {uploading ? "Uploading…" : "Analyze My Resume →"}
              </button>
              <button
                className="btn btn-ghost"
                onClick={() => router.push("/onboarding/review")}
              >
                Skip →
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
