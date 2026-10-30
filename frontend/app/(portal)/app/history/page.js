"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { apiFetch } from "@/lib/api";

const DEMO_THREADS = [
  {
    id: "t1",
    title: "What drove operating margin contraction…",
    document: "Q3_Financial_Analysis_2024.pdf",
    updated: "2h ago",
  },
  {
    id: "t2",
    title: "Summarize attention multi-head method",
    document: "Vaswani_Attention_Is_All_You_Need.pdf",
    updated: "Yesterday",
  },
  {
    id: "t3",
    title: "Primary endpoint for Cohort B",
    document: "Clinical_Trial_Protocol_v3.pdf",
    updated: "3d ago",
  },
];

function formatUpdated(value) {
  try {
    return new Date(value).toLocaleString();
  } catch {
    return String(value);
  }
}

export default function HistoryPage() {
  const [query, setQuery] = useState("");
  const [threads, setThreads] = useState(DEMO_THREADS);
  const [source, setSource] = useState("demo");
  const [exportingId, setExportingId] = useState(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await apiFetch("/threads");
        if (!res.ok) return;
        const data = await res.json();
        if (cancelled) return;
        setThreads(
          (data.items || []).map((item) => ({
            id: item.id,
            title: item.title,
            document: item.document_id ? `Document ${String(item.document_id).slice(0, 8)}` : "Deleted document",
            updated: formatUpdated(item.updated_at),
            canExport: true,
          })),
        );
        setSource("api");
      } catch {
        // keep demo threads
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return threads;
    return threads.filter(
      (item) =>
        item.title.toLowerCase().includes(q) ||
        item.document.toLowerCase().includes(q),
    );
  }, [query, threads]);

  const grouped = useMemo(() => {
    const map = new Map();
    for (const thread of filtered) {
      if (!map.has(thread.document)) map.set(thread.document, []);
      map.get(thread.document).push(thread);
    }
    return [...map.entries()];
  }, [filtered]);

  async function exportThread(threadId) {
    setExportingId(threadId);
    try {
      const res = await apiFetch(`/threads/${threadId}/export`);
      if (!res.ok) throw new Error("Export failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `folio-thread-${threadId}.md`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // ignore — demo threads have no server export
    } finally {
      setExportingId(null);
    }
  }

  return (
    <div className="mx-auto max-w-4xl px-5 py-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="display text-3xl">Chat history</h1>
          <p className="mt-2 text-sm text-[var(--text-secondary)]">
            Threads grouped by document. Search titles and source names.
            {source === "demo" ? " Demo history until Clerk session is connected." : null}
          </p>
        </div>
        <Link href="/app">
          <Button size="sm">Open workspace</Button>
        </Link>
      </div>

      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search threads…"
        className="mt-6 h-11 w-full rounded-lg border border-white/[0.08] bg-[var(--surface)] px-3 text-sm outline-none focus:border-[var(--accent)]/40"
      />

      <div className="mt-8 space-y-8">
        {grouped.map(([document, items]) => (
          <section key={document}>
            <div className="mb-3 flex items-center gap-2">
              <h2 className="text-sm text-[var(--text)]">{document}</h2>
              <Badge tone="neutral">{items.length}</Badge>
            </div>
            <div className="space-y-2">
              {items.map((thread) => (
                <div
                  key={thread.id}
                  className="flex items-center justify-between gap-3 rounded-xl border border-white/[0.07] bg-[var(--surface)] px-4 py-3"
                >
                  <Link href="/app" className="min-w-0 flex-1 transition hover:opacity-90">
                    <p className="text-sm text-[var(--text)]">{thread.title}</p>
                    <p className="mono mt-1 text-[11px] text-[var(--text-muted)]">
                      Last activity · {thread.updated}
                    </p>
                  </Link>
                  <div className="flex shrink-0 items-center gap-2">
                    {thread.canExport ? (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => exportThread(thread.id)}
                        disabled={exportingId === thread.id}
                      >
                        {exportingId === thread.id ? "…" : "Export"}
                      </Button>
                    ) : null}
                    <Link href="/app" className="text-xs text-[var(--accent)]">
                      Continue →
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </section>
        ))}
        {!grouped.length ? (
          <p className="text-sm text-[var(--text-muted)]">No threads match that search.</p>
        ) : null}
      </div>
    </div>
  );
}
