"use client";

import { useMemo, useState } from "react";
import { DOCUMENTS, SOURCES } from "@/lib/mock-data";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

function CitationChip({ marker, active, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={`Source ${marker}`}
      className={`mx-0.5 inline-flex h-5 min-w-5 items-center justify-center rounded-md px-1.5 align-middle text-[11px] font-medium ${
        active
          ? "bg-[var(--accent)] text-[#06140f]"
          : "bg-[var(--violet-soft)] text-[#c4b5fd]"
      }`}
    >
      {marker}
    </button>
  );
}

export function WorkspaceShell() {
  const [activeDoc, setActiveDoc] = useState(DOCUMENTS[0].id);
  const [activeSource, setActiveSource] = useState(1);
  const [question, setQuestion] = useState("");
  const [sourcesOpen, setSourcesOpen] = useState(true);

  const doc = useMemo(
    () => DOCUMENTS.find((item) => item.id === activeDoc) || DOCUMENTS[0],
    [activeDoc],
  );

  return (
    <div className="flex h-[calc(100vh-3rem)] min-h-[640px]">
      <section className="hidden w-[240px] shrink-0 flex-col border-r border-[var(--hairline)] bg-[var(--bg-elevated)] lg:flex">
        <div className="flex items-center justify-between px-4 py-4">
          <p className="mono text-[10px] tracking-[0.14em] text-[var(--text-muted)] uppercase">
            Documents
          </p>
          <button
            type="button"
            className="flex h-7 w-7 items-center justify-center rounded-lg border border-[var(--hairline)] text-[var(--text-secondary)] hover:text-[var(--text)]"
            aria-label="Upload document"
          >
            +
          </button>
        </div>
        <div className="space-y-1 px-2">
          {DOCUMENTS.map((item) => {
            const active = item.id === activeDoc;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setActiveDoc(item.id)}
                className={`w-full rounded-[12px] px-3 py-3 text-left transition ${
                  active
                    ? "bg-[var(--accent-soft)] border border-[var(--accent)]/30"
                    : "hover:bg-white/5"
                }`}
              >
                <p className={`truncate text-sm ${active ? "text-[var(--accent)]" : "text-[var(--text)]"}`}>
                  {item.title}
                </p>
                <p className="mt-1 text-[11px] text-[var(--text-muted)]">
                  {item.pages} pages · {item.updated}
                </p>
              </button>
            );
          })}
        </div>
        <div className="mt-auto border-t border-[var(--hairline)] p-4">
          <p className="text-xs text-[var(--text-secondary)]">Workspace Index 98.4%</p>
          <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/10">
            <div className="h-full w-[98%] rounded-full bg-[var(--accent)]" />
          </div>
          <p className="mono mt-2 text-[10px] text-[var(--text-muted)]">
            145 / 145 embed vectors cached
          </p>
        </div>
      </section>

      <section className="flex min-w-0 flex-1 flex-col">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--hairline)] px-5 py-4">
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
          <Badge tone="violet">420 t/s</Badge>
        </div>

        <div className="flex-1 space-y-5 overflow-y-auto px-5 py-6">
          <div className="ml-auto max-w-[680px] rounded-[16px] bg-[var(--surface)] px-4 py-3 text-sm">
            What were the key drivers for operating margin contraction in the international segment?
          </div>

          <div className="max-w-[680px]">
            <div className="mb-2 flex items-center gap-2">
              <Badge tone="violet">Synthesis</Badge>
            </div>
            <div className="rounded-[16px] border border-[var(--hairline)] bg-[var(--bg-elevated)] px-4 py-4 text-[15px] leading-[1.65] text-[var(--text-secondary)]">
              International operating margins contracted about 240 bps. The primary drivers were FX
              translation variances in EMEA
              <CitationChip
                marker={1}
                active={activeSource === 1}
                onClick={() => {
                  setActiveSource(1);
                  setSourcesOpen(true);
                }}
              />
              and elevated distribution logistics overhead
              <CitationChip
                marker={2}
                active={activeSource === 2}
                onClick={() => {
                  setActiveSource(2);
                  setSourcesOpen(true);
                }}
              />
              . North American manufacturing scale partially offset the pressure through fixed-cost
              absorption
              <CitationChip
                marker={3}
                active={activeSource === 3}
                onClick={() => {
                  setActiveSource(3);
                  setSourcesOpen(true);
                }}
              />
              .
            </div>
            <div className="mt-3 flex flex-wrap items-center justify-between gap-2 rounded-[12px] border border-[var(--accent)]/20 bg-[var(--accent-soft)] px-3 py-2">
              <p className="text-xs text-[var(--accent)]">
                Grounding Confidence: 99.8% (3 citations matched)
              </p>
              <div className="flex gap-2">
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

        <div className="border-t border-[var(--hairline)] p-4">
          <div className="glass mx-auto flex max-w-[720px] items-end gap-3 rounded-[20px] p-3">
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              rows={2}
              maxLength={1000}
              placeholder="Ask a question about this document..."
              className="min-h-[48px] flex-1 resize-none bg-transparent px-2 py-2 text-sm outline-none placeholder:text-[var(--text-muted)]"
            />
            <Button
              size="sm"
              aria-label="Send"
              onClick={() => setQuestion("")}
              disabled={!question.trim()}
            >
              ↑
            </Button>
          </div>
          <p className="mono mx-auto mt-2 max-w-[720px] px-2 text-[10px] text-[var(--text-muted)]">
            Using Groq Llama 3.3 70B
          </p>
        </div>
      </section>

      {sourcesOpen ? (
        <aside className="hidden w-[300px] shrink-0 flex-col border-l border-[var(--hairline)] bg-[var(--bg-elevated)] xl:flex">
          <div className="flex items-center justify-between border-b border-[var(--hairline)] px-4 py-4">
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
          <div className="space-y-3 overflow-y-auto p-3">
            {SOURCES.map((source) => {
              const active = source.marker === activeSource;
              return (
                <button
                  key={source.marker}
                  type="button"
                  onClick={() => setActiveSource(source.marker)}
                  className={`w-full rounded-[14px] border p-3 text-left transition ${
                    active
                      ? "border-[var(--accent)]/40 bg-[var(--accent-soft)]"
                      : "border-[var(--hairline)] bg-[var(--surface)] hover:border-[var(--hairline-strong)]"
                  }`}
                >
                  <p className="text-xs text-[var(--text)]">
                    [{source.marker}] Page {source.page}, {source.location}
                  </p>
                  <p className="mt-2 line-clamp-3 text-xs text-[var(--text-secondary)]">
                    {source.excerpt}
                  </p>
                  <p className="mono mt-2 text-[10px] text-[var(--text-muted)]">
                    Relevance: {source.score.toFixed(2)}
                  </p>
                </button>
              );
            })}
          </div>
        </aside>
      ) : null}
    </div>
  );
}
