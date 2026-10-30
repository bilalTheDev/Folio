"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { DOCUMENTS, SOURCES } from "@/lib/mock-data";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

function CitationChip({ marker, active, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={`Source ${marker}, open verification`}
      className={`mx-0.5 inline-flex h-5 min-w-5 items-center justify-center rounded-md px-1.5 align-middle text-[11px] font-medium transition ${
        active
          ? "bg-[var(--accent)] text-[var(--accent-ink)]"
          : "bg-[var(--accent-soft)] text-[var(--accent)] hover:bg-[var(--accent)]/25"
      }`}
    >
      {marker}
    </button>
  );
}

export function WorkspaceShell({ compactChrome = false }) {
  const [activeDoc, setActiveDoc] = useState(DOCUMENTS[0].id);
  const [activeSource, setActiveSource] = useState(1);
  const [question, setQuestion] = useState("");
  const [sourcesOpen, setSourcesOpen] = useState(true);
  const sourceRefs = useRef({});

  const doc = useMemo(
    () => DOCUMENTS.find((item) => item.id === activeDoc) || DOCUMENTS[0],
    [activeDoc],
  );

  useEffect(() => {
    const el = sourceRefs.current[activeSource];
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [activeSource]);

  function selectSource(marker) {
    setActiveSource(marker);
    setSourcesOpen(true);
  }

  return (
    <div
      className={`flex bg-[var(--bg)] ${
        compactChrome ? "h-[calc(100vh-3.25rem)]" : "h-full min-h-[640px]"
      }`}
    >
      {/* Document roster */}
      <section className="hidden w-60 shrink-0 flex-col border-r border-white/[0.06] bg-[var(--bg-chrome)] lg:flex">
        <div className="flex items-center justify-between px-4 py-4">
          <p className="mono text-[10px] tracking-[0.16em] text-[var(--text-muted)] uppercase">
            Documents
          </p>
          <button
            type="button"
            className="flex h-7 w-7 items-center justify-center rounded-md border border-white/[0.08] text-[var(--text-secondary)] hover:text-[var(--text)]"
            aria-label="Upload document"
          >
            +
          </button>
        </div>
        <div className="min-h-0 flex-1 space-y-1 overflow-y-auto px-2">
          {DOCUMENTS.map((item) => {
            const active = item.id === activeDoc;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setActiveDoc(item.id)}
                className={`w-full rounded-lg px-3 py-3 text-left transition ${
                  active
                    ? "border border-[var(--accent)]/30 bg-[var(--accent-soft)]"
                    : "hover:bg-white/[0.03]"
                }`}
              >
                <p
                  className={`truncate text-sm ${
                    active ? "text-[var(--accent)]" : "text-[var(--text)]"
                  }`}
                >
                  {item.title}
                </p>
                <p className="mt-1 text-[11px] text-[var(--text-muted)]">
                  {item.pages} pages · {item.updated}
                </p>
              </button>
            );
          })}
        </div>
        <div className="border-t border-white/[0.06] p-4">
          <p className="text-xs text-[var(--text-secondary)]">Workspace Index: 98.4%</p>
          <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/10">
            <div className="h-full w-[98%] rounded-full bg-[var(--accent)]" />
          </div>
          <p className="mono mt-2 text-[10px] text-[var(--text-muted)]">
            145 / 145 vectors cached in RAM
          </p>
        </div>
      </section>

      {/* Synthesis column */}
      <section className="flex min-w-0 flex-1 flex-col">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.06] px-6 py-4">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="display text-xl text-[var(--text)]">
                {doc.title.replace(".pdf", "").replaceAll("_", " ")}
              </h1>
              <Badge tone="accent">Verified</Badge>
            </div>
            <p className="mt-1 text-xs text-[var(--text-muted)]">
              {doc.pages} pages · Indexed via Groq Llama 3.3
            </p>
          </div>
          <Badge tone="cyan">420 tok/sec</Badge>
        </div>

        <div className="flex-1 space-y-5 overflow-y-auto px-6 py-6 md:px-8">
          <div className="ml-auto max-w-[680px] rounded-lg bg-[var(--surface)] px-4 py-3 text-sm text-[var(--text)]">
            What were the key drivers for operating margin contraction in the international
            segment?
          </div>

          <div className="max-w-[680px] fade-up">
            <p className="mono mb-2 text-[11px] tracking-[0.14em] text-[var(--text-muted)] uppercase">
              ✦ Synthesis
            </p>
            <div className="rounded-lg border border-white/[0.07] bg-[var(--surface)] px-4 py-4 text-[15px] leading-[1.7] text-[var(--text-secondary)]">
              International operating margins contracted about 240 bps. The primary drivers were FX
              translation variances in EMEA
              <CitationChip
                marker={1}
                active={activeSource === 1}
                onClick={() => selectSource(1)}
              />
              and elevated distribution logistics overhead
              <CitationChip
                marker={2}
                active={activeSource === 2}
                onClick={() => selectSource(2)}
              />
              . North American manufacturing scale partially offset the pressure through fixed-cost
              absorption
              <CitationChip
                marker={3}
                active={activeSource === 3}
                onClick={() => selectSource(3)}
              />
              .
            </div>
            <div className="mt-3 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-[var(--accent)]/20 bg-[var(--accent-soft)] px-3 py-2">
              <p className="text-xs text-[var(--accent)]">
                ✓ Grounding Confidence: 99.8% (3 citations matched)
              </p>
              <div className="flex gap-1">
                <Button size="sm" variant="ghost">
                  Copy
                </Button>
                <Button size="sm" variant="ghost">
                  Export
                </Button>
              </div>
            </div>
          </div>
        </div>

        <div className="border-t border-white/[0.06] p-4">
          <div className="mx-auto flex max-w-[720px] items-end gap-3 rounded-xl border border-white/[0.1] bg-[var(--surface)] p-3">
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              rows={2}
              maxLength={1000}
              placeholder="Ask a question about this document..."
              className="min-h-[48px] flex-1 resize-none bg-transparent px-2 py-2 text-sm outline-none placeholder:text-[var(--text-muted)]"
            />
            <Button
              size="icon"
              aria-label="Send question"
              onClick={() => setQuestion("")}
              disabled={!question.trim()}
              className="shrink-0"
            >
              ↑
            </Button>
          </div>
          <p className="mono mx-auto mt-2 max-w-[720px] px-2 text-[10px] text-[var(--text-muted)]">
            ⚡ Using Groq Llama 3.3 70B
          </p>
        </div>
      </section>

      {/* Sources drawer */}
      {sourcesOpen ? (
        <aside className="hidden w-80 shrink-0 flex-col border-l border-white/[0.06] bg-[var(--bg-chrome)] xl:flex">
          <div className="flex items-center justify-between border-b border-white/[0.06] px-4 py-4">
            <p className="text-sm text-[var(--text)]">Sources ({SOURCES.length} items)</p>
            <button
              type="button"
              className="text-[var(--text-muted)] hover:text-[var(--text)]"
              onClick={() => setSourcesOpen(false)}
              aria-label="Close sources"
            >
              ×
            </button>
          </div>
          <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-4">
            {SOURCES.map((source) => {
              const active = source.marker === activeSource;
              return (
                <button
                  key={source.marker}
                  type="button"
                  ref={(node) => {
                    sourceRefs.current[source.marker] = node;
                  }}
                  onClick={() => selectSource(source.marker)}
                  className={`w-full rounded-lg border p-3 text-left transition ${
                    active
                      ? "emerald-glow border-[var(--accent)]/40 bg-[var(--accent-soft)]"
                      : "border-white/[0.07] bg-[var(--surface)] hover:border-white/[0.12]"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-xs text-[var(--text)]">
                      [{source.marker}] Page {source.page}, {source.location}
                    </p>
                    <span className="text-[var(--accent)]" aria-hidden>
                      ✓
                    </span>
                  </div>
                  <p className="mt-2 text-xs leading-relaxed text-[var(--text-secondary)]">
                    “{source.excerpt}”
                  </p>
                  <div className="mono mt-3 flex items-center justify-between text-[10px] text-[var(--text-muted)]">
                    <span>Relevance: {source.score.toFixed(2)}</span>
                    <span className="text-[var(--accent)]">View in page ↗</span>
                  </div>
                </button>
              );
            })}
          </div>
        </aside>
      ) : (
        <button
          type="button"
          onClick={() => setSourcesOpen(true)}
          className="hidden w-10 shrink-0 items-center justify-center border-l border-white/[0.06] text-xs text-[var(--text-muted)] hover:text-[var(--accent)] xl:flex"
          aria-label="Open sources"
        >
          ›
        </button>
      )}
    </div>
  );
}
