"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Toggle } from "@/components/ui/Toggle";
import { getProviderKey, saveProviderKey } from "@/lib/api";

const PROVIDERS = [
  { id: "groq", label: "Groq", meta: "38ms TTFT · Active" },
  { id: "cerebras", label: "Cerebras", meta: "Standby" },
  { id: "novita", label: "Novita", meta: "Open models" },
  { id: "huggingface", label: "HF TGI", meta: "Router" },
];

export function SettingsPage() {
  const [provider, setProvider] = useState("groq");
  const [ephemeral, setEphemeral] = useState(true);
  const [opfs, setOpfs] = useState(true);
  const [reducedMotion, setReducedMotion] = useState(false);
  const [theme, setTheme] = useState("dark");
  const [threshold, setThreshold] = useState(99.5);
  const [fontSize, setFontSize] = useState(16);
  const [reveal, setReveal] = useState(false);
  const [keyInput, setKeyInput] = useState("");
  const [keyStatus, setKeyStatus] = useState("");

  useEffect(() => {
    setKeyInput(getProviderKey());
  }, []);

  function handleSaveKey() {
    saveProviderKey(keyInput.trim());
    setKeyStatus(keyInput.trim() ? "Saved for this browser session." : "Key cleared.");
  }

  return (
    <div className="mx-auto max-w-6xl px-5 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="display text-3xl text-[var(--text)]">Account & Preferences</h1>
          <p className="mt-2 max-w-2xl text-sm text-[var(--text-secondary)]">
            Manage your personal identity, high-throughput Bring-Your-Own-Key credentials, and
            cryptographic privacy parameters.
          </p>
        </div>
        <Button>✓ Save Changes</Button>
      </div>

      <div className="mt-8 grid gap-5 lg:grid-cols-[1.4fr_1fr]">
        <div className="space-y-5">
          <section className="surface-card p-5">
            <div className="flex items-start gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-full border border-white/[0.08] bg-[var(--surface-elevated)] text-sm text-[var(--text-secondary)]">
                ER
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-lg text-[var(--text)]">Elena Rostova, PhD</h2>
                  <Badge tone="accent">Pro Researcher</Badge>
                  <Badge tone="cyan">BYOK Active</Badge>
                </div>
                <p className="mt-1 text-sm text-[var(--text-secondary)]">
                  Principal Research Fellow
                </p>
                <p className="mono mt-2 text-xs text-[var(--text-muted)]">
                  e.rostova@oxon.ac.uk · PGP Signed
                </p>
              </div>
            </div>
          </section>

          <section className="surface-card p-5">
            <h2 className="text-base text-[var(--text)]">Inference Architecture (BYOK)</h2>
            <div className="mt-4 grid grid-cols-2 gap-2 md:grid-cols-4">
              {PROVIDERS.map((item) => {
                const active = item.id === provider;
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setProvider(item.id)}
                    className={`rounded-lg border px-3 py-3 text-left transition ${
                      active
                        ? "border-[var(--accent)]/40 bg-[var(--accent-soft)]"
                        : "border-white/[0.07] bg-[var(--bg-chrome)] hover:border-white/[0.12]"
                    }`}
                  >
                    <p
                      className={`text-sm ${
                        active ? "text-[var(--accent)]" : "text-[var(--text)]"
                      }`}
                    >
                      {item.label}
                    </p>
                    <p className="mt-1 text-[11px] text-[var(--text-muted)]">{item.meta}</p>
                  </button>
                );
              })}
            </div>

            <div className="mt-5">
              <div className="relative">
                <Input
                  label="Groq Cloud Secret Key"
                  type={reveal ? "text" : "password"}
                  value={keyInput}
                  onChange={(e) => setKeyInput(e.target.value)}
                  placeholder="gsk_…"
                />
                <button
                  type="button"
                  className="absolute top-8 right-3 text-xs text-[var(--text-muted)] hover:text-[var(--text)]"
                  onClick={() => setReveal((v) => !v)}
                >
                  {reveal ? "Hide" : "Reveal"}
                </button>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <Button size="sm" variant="dark" onClick={handleSaveKey}>
                  Update
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => {
                    setKeyInput("");
                    saveProviderKey("");
                    setKeyStatus("Key cleared.");
                  }}
                >
                  Remove
                </Button>
              </div>
              <p className="mono mt-2 text-[10px] text-[var(--text-muted)]">
                Stored in sessionStorage for this browser tab · sent as X-Provider-Key
              </p>
              {keyStatus ? (
                <p className="mt-2 text-xs text-[var(--accent)]">{keyStatus}</p>
              ) : null}
            </div>

            <label className="mt-5 block">
              <span className="mono text-[11px] tracking-[0.14em] text-[var(--text-secondary)] uppercase">
                Default Grounding Model
              </span>
              <select className="mt-2 h-11 w-full rounded-lg border border-white/[0.08] bg-[var(--bg-chrome)] px-3 text-sm outline-none">
                <option>llama-3.3-70b-versatile (Context: 128k)</option>
                <option>llama-3.1-8b-instant</option>
              </select>
            </label>

            <div className="mt-5 rounded-lg border border-white/[0.06] bg-[var(--bg-chrome)] p-3">
              <div className="flex items-center justify-between">
                <p className="mono text-[10px] tracking-[0.12em] text-[var(--text-muted)] uppercase">
                  Realtime Inference Pulse
                </p>
                <p className="mono text-[10px] text-[var(--accent)]">p99 44ms · 0 Drop</p>
              </div>
              <div className="mt-3 flex h-10 items-end gap-1">
                {[40, 55, 35, 70, 48, 62, 44, 80, 52, 66, 38, 72, 50, 58, 46, 74].map(
                  (h, i) => (
                    <span
                      key={i}
                      className="flex-1 rounded-sm bg-[var(--accent)]/70"
                      style={{ height: `${h}%` }}
                    />
                  ),
                )}
              </div>
            </div>
          </section>

          <section className="surface-card p-5">
            <h2 className="text-base text-[var(--text)]">Synthesis Portability</h2>
            <div className="mt-4 grid gap-3 md:grid-cols-3">
              {[
                { ext: ".JSON", desc: "Complete Graph", meta: "14.2 MB · With vectors" },
                { ext: ".BIB", desc: "BibTeX Index", meta: "142 Citations verified" },
                { ext: ".PDF", desc: "Archival Folio", meta: "Typeset report" },
              ].map((item) => (
                <button
                  key={item.ext}
                  type="button"
                  className="rounded-lg border border-white/[0.07] bg-[var(--bg-chrome)] p-3 text-left transition hover:border-white/[0.12]"
                >
                  <p className="text-sm text-[var(--text)]">{item.ext}</p>
                  <p className="mt-1 text-xs text-[var(--text-secondary)]">{item.desc}</p>
                  <p className="mono mt-2 text-[10px] text-[var(--text-muted)]">{item.meta}</p>
                </button>
              ))}
            </div>
          </section>
        </div>

        <div className="space-y-5">
          <section className="surface-card p-5">
            <h2 className="text-base text-[var(--text)]">Privacy Guardrails</h2>
            <div className="mt-4 space-y-5">
              <Toggle
                checked={ephemeral}
                onChange={setEphemeral}
                label="Ephemeral RAM Buffer"
                description="Flush source texts and vector contexts after 60 min session idle."
              />
              <div>
                <div className="mb-2 flex items-center justify-between text-sm">
                  <span>Strict Grounding Threshold</span>
                  <span className="mono text-[var(--accent)]">{threshold.toFixed(1)}%</span>
                </div>
                <input
                  type="range"
                  min="90"
                  max="99.9"
                  step="0.1"
                  value={threshold}
                  onChange={(e) => setThreshold(Number(e.target.value))}
                  className="w-full accent-[var(--accent)]"
                />
                <p className="mt-2 text-xs text-[var(--text-muted)]">
                  Minimum semantic overlap before a sentence receives a citation footnote.
                </p>
              </div>
              <Toggle
                checked={opfs}
                onChange={setOpfs}
                label="Client-Side OPFS Indexing"
                description="Store document chunks in Origin Private File System."
              />
            </div>
          </section>

          <section className="surface-card p-5">
            <h2 className="text-base text-[var(--text)]">Quiet Ergonomics</h2>
            <div className="mt-4 grid grid-cols-2 gap-2">
              {[
                { id: "dark", label: "Quiet Dark" },
                { id: "light", label: "Quiet Light" },
                { id: "system", label: "System" },
              ].map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => {
                    setTheme(item.id);
                    try {
                      window.localStorage.setItem("folio_theme", item.id);
                      const resolved =
                        item.id === "system"
                          ? window.matchMedia("(prefers-color-scheme: light)").matches
                            ? "light"
                            : "dark"
                          : item.id;
                      document.documentElement.setAttribute("data-theme", resolved);
                    } catch {
                      // ignore storage failures
                    }
                  }}
                  className={`rounded-lg border px-3 py-3 text-sm transition ${
                    theme === item.id
                      ? "border-[var(--accent)]/40 bg-[var(--accent-soft)] text-[var(--accent)]"
                      : "border-white/[0.07] text-[var(--text-secondary)]"
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>
            <div className="mt-5">
              <Toggle
                checked={reducedMotion}
                onChange={setReducedMotion}
                label="Reduced Kinetic Motion"
                description="Disable ambient particle shifts."
              />
            </div>
            <div className="mt-5 flex items-center justify-between">
              <span className="text-sm">Reading Serif Size</span>
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="dark"
                  onClick={() => setFontSize((v) => Math.max(14, v - 1))}
                >
                  A−
                </Button>
                <span className="mono text-xs text-[var(--text-muted)]">{fontSize}px</span>
                <Button
                  size="sm"
                  variant="dark"
                  onClick={() => setFontSize((v) => Math.min(20, v + 1))}
                >
                  A+
                </Button>
              </div>
            </div>
          </section>

          <section className="rounded-xl border border-[var(--danger)]/30 bg-[var(--danger-soft)] p-5">
            <h2 className="text-base text-[var(--danger)]">Irreversible Operations</h2>
            <p className="mt-2 text-xs text-[var(--text-secondary)]">
              Immediately deletes encrypted session state, destroys remote embedding cache, and
              revokes remembered BYOK keys.
            </p>
            <Button variant="danger" className="mt-4">
              Purge Vector Vault
            </Button>
          </section>
        </div>
      </div>
    </div>
  );
}
