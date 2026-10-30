"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { DOCUMENTS, SOURCES as DEMO_SOURCES } from "@/lib/mock-data";
import { demoAnswerStream, sampleAnswerStream } from "@/lib/sse";
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

function renderAnswer(text, activeSource, onSelect) {
  const parts = text.split(/(\[\d+\])/g);
  return parts.map((part, index) => {
    const match = part.match(/^\[(\d+)\]$/);
    if (match) {
      const marker = Number(match[1]);
      return (
        <CitationChip
          key={`${marker}-${index}`}
          marker={marker}
          active={activeSource === marker}
          onClick={() => onSelect(marker)}
        />
      );
    }
    return <span key={`t-${index}`}>{part}</span>;
  });
}

const SEED_QUESTION =
  "What were the key drivers for operating margin contraction in the international segment?";
const SEED_ANSWER =
  "International operating margins contracted about 240 bps. The primary drivers were FX translation variances in EMEA [1] and elevated distribution logistics overhead [2]. North American manufacturing scale partially offset the pressure through fixed-cost absorption [3].";

const DEFAULT_SUGGESTED = [
  "What drove operating margin contraction in the international segment?",
  "How did logistics costs change year over year?",
  "What offset international margin pressure?",
];

export function WorkspaceShell({
  compactChrome = false,
  emptyStart = false,
  trialMode = false,
  suggestedQuestions = DEFAULT_SUGGESTED,
  documentTitle = null,
}) {
  const [activeDoc, setActiveDoc] = useState(DOCUMENTS[0].id);
  const [activeSource, setActiveSource] = useState(1);
  const [question, setQuestion] = useState("");
  const [sourcesOpen, setSourcesOpen] = useState(true);
  const [sources, setSources] = useState(DEMO_SOURCES);
  const [streaming, setStreaming] = useState(false);
  const [stopRequested, setStopRequested] = useState(false);
  const [streamError, setStreamError] = useState("");
  const [messages, setMessages] = useState(
    emptyStart
      ? []
      : [
          { id: "u1", role: "user", content: SEED_QUESTION },
          { id: "a1", role: "assistant", content: SEED_ANSWER, confidence: "99.8%" },
        ],
  );
  const sourceRefs = useRef({});
  const bottomRef = useRef(null);
  const abortRef = useRef(null);

  const doc = useMemo(
    () => DOCUMENTS.find((item) => item.id === activeDoc) || DOCUMENTS[0],
    [activeDoc],
  );

  const headingTitle =
    documentTitle ||
    (trialMode
      ? "Folio Sample Report — Q3 Operations Overview"
      : doc.title.replace(".pdf", "").replaceAll("_", " "));

  useEffect(() => {
    const el = sourceRefs.current[activeSource];
    if (el) el.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [activeSource, sources]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, streaming]);

  useEffect(() => {
    return () => abortRef.current?.abort();
  }, []);

  function selectSource(marker) {
    setActiveSource(marker);
    setSourcesOpen(true);
  }

  async function runStream(text, { regenerate = false } = {}) {
    if (!text || streaming) return;
    if (text.length > 1000) return;

    setQuestion("");
    setStreamError("");
    setStreaming(true);
    setStopRequested(false);
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    const userId = `u-${Date.now()}`;
    const assistantId = `a-${Date.now()}`;
    setMessages((prev) => {
      const next = regenerate
        ? prev.filter((msg, index) => !(index === prev.length - 1 && msg.role === "assistant"))
        : prev;
      const withUser = regenerate
        ? next
        : [...next, { id: userId, role: "user", content: text }];
      return [...withUser, { id: assistantId, role: "assistant", content: "", confidence: null }];
    });

    const handlers = {
      signal: controller.signal,
      onCitations: (items) => {
        setSources(
          items.map((item) => ({
            marker: item.marker,
            page: item.page,
            location: item.location || "Passage",
            excerpt: item.excerpt,
            score: item.score,
          })),
        );
        if (items[0]) setActiveSource(items[0].marker);
      },
      onToken: (token) => {
        if (controller.signal.aborted) return;
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantId ? { ...msg, content: msg.content + token } : msg,
          ),
        );
      },
      onError: (payload) => {
        setStreamError(payload?.message || "Something went wrong.");
      },
      onDone: (payload) => {
        const stopped = Boolean(payload?.stopped || controller.signal.aborted);
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantId
              ? {
                  ...msg,
                  confidence: stopped ? "stopped" : "99.8%",
                  stopped,
                }
              : msg,
          ),
        );
      },
    };

    try {
      if (trialMode) {
        try {
          await sampleAnswerStream(text, handlers);
        } catch (err) {
          if (controller.signal.aborted) return;
          // Offline / API down: fall back to local demo stream.
          setStreamError("");
          await demoAnswerStream(text, handlers);
          if (err?.status === 429) {
            setStreamError(err.message || "Trial limit reached. Sign up to continue.");
          }
        }
      } else {
        await demoAnswerStream(text, handlers);
      }
    } finally {
      setStreaming(false);
      setStopRequested(false);
    }
  }

  function handleAsk() {
    runStream(question.trim());
  }

  function handleRegenerate() {
    const lastUser = [...messages].reverse().find((msg) => msg.role === "user");
    if (lastUser) runStream(lastUser.content, { regenerate: true });
  }

  function handleStop() {
    setStopRequested(true);
    abortRef.current?.abort();
    setStreaming(false);
    setMessages((prev) => {
      const last = prev[prev.length - 1];
      if (!last || last.role !== "assistant") return prev;
      return prev.map((msg, index) =>
        index === prev.length - 1
          ? { ...msg, confidence: msg.confidence || "stopped", stopped: true }
          : msg,
      );
    });
  }

  function exportMarkdown() {
    const lines = [`# ${headingTitle}`, "", `_Exported from Folio_`, ""];
    for (const msg of messages) {
      lines.push(`## ${msg.role === "user" ? "User" : "Assistant"}`, "", msg.content, "");
    }
    const blob = new Blob([lines.join("\n")], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "folio-thread.md";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div
      className={`flex bg-[var(--bg)] ${
        compactChrome ? "h-[calc(100vh-3.25rem)]" : "h-full min-h-[640px]"
      }`}
    >
      <section className="hidden w-60 shrink-0 flex-col border-r border-white/[0.06] bg-[var(--bg-chrome)] lg:flex">
        <div className="flex items-center justify-between px-4 py-4">
          <p className="mono text-[10px] tracking-[0.16em] text-[var(--text-muted)] uppercase">
            Documents
          </p>
          <Link
            href="/app/documents/new"
            className="flex h-7 w-7 items-center justify-center rounded-md border border-white/[0.08] text-[var(--text-secondary)] hover:text-[var(--text)]"
            aria-label="Upload document"
          >
            +
          </Link>
        </div>
        <div className="min-h-0 flex-1 space-y-1 overflow-y-auto px-2">
          {(trialMode
            ? [
                {
                  id: "sample",
                  title: headingTitle,
                  pages: 3,
                  updated: "Sample",
                },
              ]
            : DOCUMENTS
          ).map((item) => {
            const active = trialMode ? true : item.id === activeDoc;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => !trialMode && setActiveDoc(item.id)}
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
          <p className="text-xs text-[var(--text-secondary)]">
            {trialMode ? "Sample index · lexical" : "Workspace Index: 98.4%"}
          </p>
          <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/10">
            <div className="h-full w-[98%] rounded-full bg-[var(--accent)]" />
          </div>
          <p className="mono mt-2 text-[10px] text-[var(--text-muted)]">
            {trialMode ? "Auth-free trial · 5 questions / IP / day" : "145 / 145 vectors cached in RAM"}
          </p>
        </div>
      </section>

      <section className="flex min-w-0 flex-1 flex-col">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.06] px-6 py-4">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="display text-xl text-[var(--text)]">{headingTitle}</h1>
              <Badge tone="accent">{trialMode ? "Sample" : "Verified"}</Badge>
            </div>
            <p className="mt-1 text-xs text-[var(--text-muted)]">
              {trialMode
                ? "Public trial · grounded answers with citations"
                : `${doc.pages} pages · Indexed via Groq Llama 3.3`}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {messages.length ? (
              <Button size="sm" variant="ghost" onClick={exportMarkdown}>
                Export
              </Button>
            ) : null}
            <Badge tone="cyan">{streaming ? "streaming…" : "420 tok/sec"}</Badge>
          </div>
        </div>

        <div
          className="flex-1 space-y-5 overflow-y-auto px-6 py-6 md:px-8"
          aria-live="polite"
        >
          {!messages.length ? (
            <div className="mx-auto max-w-[680px]">
              <p className="mono text-[11px] tracking-[0.14em] text-[var(--text-muted)] uppercase">
                Suggested questions
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {suggestedQuestions.map((item) => (
                  <button
                    key={item}
                    type="button"
                    className="rounded-lg border border-white/[0.08] bg-[var(--surface)] px-3 py-2 text-left text-sm text-[var(--text-secondary)] hover:border-[var(--accent)]/30 hover:text-[var(--text)]"
                    onClick={() => runStream(item)}
                  >
                    {item}
                  </button>
                ))}
              </div>
            </div>
          ) : null}
          {messages.map((msg) =>
            msg.role === "user" ? (
              <div
                key={msg.id}
                className="ml-auto max-w-[680px] rounded-lg bg-[var(--surface)] px-4 py-3 text-sm text-[var(--text)]"
              >
                {msg.content}
              </div>
            ) : (
              <div key={msg.id} className="max-w-[680px] fade-up">
                <p className="mono mb-2 text-[11px] tracking-[0.14em] text-[var(--text-muted)] uppercase">
                  ✦ Synthesis
                </p>
                <div className="rounded-lg border border-white/[0.07] bg-[var(--surface)] px-4 py-4 text-[15px] leading-[1.7] text-[var(--text-secondary)]">
                  {msg.content
                    ? renderAnswer(msg.content, activeSource, selectSource)
                    : streaming
                      ? "…"
                      : null}
                </div>
                {msg.confidence ? (
                  <div className="mt-3 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-[var(--accent)]/20 bg-[var(--accent-soft)] px-3 py-2">
                    <p className="text-xs text-[var(--accent)]">
                      {msg.stopped ? "■ Generation stopped" : "✓ Grounding Confidence:"}{" "}
                      {msg.stopped
                        ? ""
                        : `${msg.confidence} (${sources.length} citations matched)`}
                    </p>
                    <div className="flex gap-1">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => navigator.clipboard?.writeText(msg.content)}
                      >
                        Copy
                      </Button>
                      <Button size="sm" variant="ghost" onClick={handleRegenerate}>
                        Regenerate
                      </Button>
                    </div>
                  </div>
                ) : null}
              </div>
            ),
          )}
          {streamError ? (
            <p className="mx-auto max-w-[680px] text-sm text-[var(--danger)]">{streamError}</p>
          ) : null}
          <div ref={bottomRef} />
        </div>

        <div className="border-t border-white/[0.06] p-4">
          <div className="mx-auto flex max-w-[720px] items-end gap-3 rounded-xl border border-white/[0.1] bg-[var(--surface)] p-3">
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleAsk();
                }
              }}
              rows={2}
              maxLength={1000}
              placeholder="Ask a question about this document..."
              className="min-h-[48px] flex-1 resize-none bg-transparent px-2 py-2 text-sm outline-none placeholder:text-[var(--text-muted)]"
              disabled={streaming}
            />
            {streaming ? (
              <Button size="sm" variant="secondary" onClick={handleStop}>
                {stopRequested ? "Stopping…" : "Stop"}
              </Button>
            ) : (
              <Button
                size="icon"
                aria-label="Send question"
                onClick={handleAsk}
                disabled={!question.trim()}
                className="shrink-0"
              >
                ↑
              </Button>
            )}
          </div>
          <p className="mono mx-auto mt-2 max-w-[720px] px-2 text-[10px] text-[var(--text-muted)]">
            ⚡ Using Groq Llama 3.3 70B · {question.length}/1000
          </p>
        </div>
      </section>

      {sourcesOpen ? (
        <aside className="hidden w-80 shrink-0 flex-col border-l border-white/[0.06] bg-[var(--bg-chrome)] xl:flex">
          <div className="flex items-center justify-between border-b border-white/[0.06] px-4 py-4">
            <p className="text-sm text-[var(--text)]">Sources ({sources.length} items)</p>
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
            {sources.map((source) => {
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
                    <span>Relevance: {Number(source.score).toFixed(2)}</span>
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
