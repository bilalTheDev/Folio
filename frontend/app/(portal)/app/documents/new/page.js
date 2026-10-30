"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { uploadDocument } from "@/lib/api/documents";

const STEPS = ["validating", "extracting", "embedding", "ready"];

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [mode, setMode] = useState("");

  function acceptFile(next) {
    setError("");
    if (!next) return;
    const name = next.name.toLowerCase();
    const ok =
      name.endsWith(".pdf") || name.endsWith(".docx") || name.endsWith(".txt");
    if (!ok) {
      setError("Only PDF, DOCX, and TXT files are supported.");
      return;
    }
    if (next.size > 10 * 1024 * 1024) {
      setError("File exceeds the 10 MB limit.");
      return;
    }
    setFile(next);
  }

  async function runDemoSteps() {
    for (const step of STEPS) {
      setStatus(step);
      await new Promise((r) => setTimeout(r, step === "embedding" ? 900 : 450));
    }
  }

  async function startIngest() {
    if (!file) return;
    setError("");
    setMode("");

    setStatus("validating");
    try {
      setStatus("extracting");
      const doc = await uploadDocument(file);
      setMode("api");
      setStatus("embedding");
      await new Promise((r) => setTimeout(r, 150));
      setStatus("ready");
      router.push(doc?.id ? `/app?doc=${doc.id}` : "/app");
      return;
    } catch (err) {
      const message = err?.message || "Upload failed";
      if (/sign in|unauthorized|401|403/i.test(message)) {
        setMode("demo");
        await runDemoSteps();
        setError("Sign in required for live ingest — demo indexing finished.");
        return;
      }
      if (/unreachable|failed to fetch|network/i.test(message)) {
        setMode("demo");
        await runDemoSteps();
        setError("API unreachable — demo indexing finished.");
        return;
      }
      setStatus("idle");
      setError(message);
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-5 py-8">
      <Link href="/app/library" className="text-sm text-[var(--text-secondary)] hover:text-[var(--text)]">
        ← Document Vault
      </Link>
      <h1 className="display mt-4 text-3xl">Upload a document</h1>
      <p className="mt-2 text-sm text-[var(--text-secondary)]">
        PDF, DOCX, or TXT · max 10 MB · 100 pages · selectable text required
      </p>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          acceptFile(e.dataTransfer.files?.[0]);
        }}
        className={`mt-8 rounded-xl border border-dashed p-10 text-center transition ${
          dragOver
            ? "border-[var(--accent)] bg-[var(--accent-soft)]"
            : "border-white/[0.12] bg-[var(--surface)]"
        }`}
      >
        <p className="text-sm text-[var(--text)]">Drag a file here, or choose one</p>
        <label className="mt-4 inline-flex cursor-pointer">
          <span className="rounded-lg bg-[var(--accent)] px-4 py-2 text-sm font-medium text-[var(--accent-ink)]">
            Browse files
          </span>
          <input
            type="file"
            accept=".pdf,.docx,.txt,application/pdf,text/plain"
            className="hidden"
            onChange={(e) => acceptFile(e.target.files?.[0])}
          />
        </label>
        {file ? (
          <p className="mono mt-4 text-xs text-[var(--text-muted)]">
            {file.name} · {(file.size / 1024).toFixed(1)} KB
          </p>
        ) : null}
      </div>

      {error ? <p className="mt-4 text-sm text-[var(--danger)]">{error}</p> : null}

      {status !== "idle" ? (
        <div className="mt-6 space-y-2">
          {STEPS.map((step) => {
            const currentIndex = STEPS.indexOf(status);
            const stepIndex = STEPS.indexOf(step);
            const done = stepIndex < currentIndex || status === "ready";
            const active = step === status;
            return (
              <div
                key={step}
                className="flex items-center justify-between rounded-lg border border-white/[0.07] bg-[var(--bg-chrome)] px-3 py-2"
              >
                <span className="text-sm capitalize text-[var(--text-secondary)]">{step}</span>
                <Badge tone={done || active ? "accent" : "neutral"}>
                  {done ? "done" : active ? "…" : "queued"}
                </Badge>
              </div>
            );
          })}
        </div>
      ) : null}

      <div className="mt-6 flex gap-3">
        <Button
          onClick={() => {
            if (status === "ready") router.push("/app");
            else startIngest();
          }}
          disabled={!file || (status !== "idle" && status !== "ready")}
        >
          {status === "ready" ? "Open workspace" : "Start indexing"}
        </Button>
        <Button
          variant="ghost"
          onClick={() => {
            setFile(null);
            setStatus("idle");
            setError("");
            setMode("");
          }}
        >
          Reset
        </Button>
      </div>
      <p className="mono mt-4 text-[11px] text-[var(--text-muted)]">
        Posts to POST /api/documents when authenticated. Without a session, runs a local demo
        pipeline ({mode || "idle"}).
      </p>
    </div>
  );
}
