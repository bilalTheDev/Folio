"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { WorkspaceShell } from "@/components/workspace/WorkspaceShell";
import { Button } from "@/components/ui/Button";
import { apiFetch } from "@/lib/api/client";

const FALLBACK_SUGGESTED = [
  "What drove operating margin contraction in the international segment?",
  "How did logistics costs change year over year?",
  "What offset international margin pressure?",
];

export default function TryPage() {
  const [sampleTitle, setSampleTitle] = useState("Folio Sample Report — Q3 Operations Overview");
  const [suggested, setSuggested] = useState(FALLBACK_SUGGESTED);

  useEffect(() => {
    apiFetch("/sample")
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (!data) return;
        if (data.title) setSampleTitle(data.title);
        if (Array.isArray(data.suggested_questions) && data.suggested_questions.length) {
          setSuggested(data.suggested_questions);
        }
      })
      .catch(() => {});
  }, []);

  return (
    <div className="min-h-screen bg-[var(--bg)]">
      <div className="flex items-center justify-between border-b border-white/[0.06] px-5 py-3">
        <p className="text-sm text-[var(--text-secondary)]">
          {sampleTitle} · IP-limited trial · sign up to upload your own
        </p>
        <div className="flex gap-2">
          <Link href="/login">
            <Button size="sm">Sign up</Button>
          </Link>
          <Link href="/">
            <Button size="sm" variant="ghost">
              Home
            </Button>
          </Link>
        </div>
      </div>
      <WorkspaceShell
        compactChrome
        emptyStart
        trialMode
        documentTitle={sampleTitle}
        suggestedQuestions={suggested}
      />
    </div>
  );
}
