"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Toggle } from "@/components/ui/Toggle";

const PROVIDERS = [
  { id: "groq", label: "Groq", meta: "38ms TTFT" },
  { id: "cerebras", label: "Cerebras", meta: "Fast wafer" },
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

  return (
    <div className="mx-auto max-w-6xl px-5 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="display text-3xl text-[var(--text)]">Account & Preferences</h1>
          <p className="mt-2 max-w-2xl text-sm text-[var(--text-secondary)]">
            Manage your identity, Bring-Your-Own-Key credentials, and privacy parameters.
          </p>
        </div>
        <Button>Save Changes</Button>
      </div>

      <div className="mt-8 grid gap-5 lg:grid-cols-[1.4fr_1fr]">
        <div className="space-y-5">
          <section className="rounded-[16px] border border-[var(--hairline)] bg-[var(--surface)] p-5">
            <div className="flex items-start gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[var(--violet-soft)] text-sm text-[#c4b5fd]">
                ER
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-lg text-[var(--text)]">Elena Rostova, PhD</h2>
                  <Badge tone="accent">Pro Researcher</Badge>
                  <Badge tone="violet">BYOK Active</Badge>
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

          <section className="rounded-[16px] border border-[var(--hairline)] bg-[var(--surface)] p-5">
            <h2 className="text-base text-[var(--text)]">Inference Architecture (BYOK)</h2>
            <div className="mt-4 grid grid-cols-2 gap-2 md:grid-cols-4">
              {PROVIDERS.map((item) => {
                const active = item.id === provider;
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setProvider(item.id)}
                    className={`rounded-[12px] border px-3 py-3 text-left ${
                      active
                        ? "border-[var(--accent)]/40 bg-[var(--accent-soft)]"
                        : "border-[var(--hairline)] bg-[var(--bg-elevated)]"
                    }`}
                  >
                    <p className={`text-sm ${active ? "text-[var(--accent)]" : "text-[var(--text)]"}`}>
                      {item.label}
                    </p>
                    <p className="mt-1 text-[11px] text-[var(--text-muted)]">{item.meta}</p>
                  </button>
                );
              })}
            </div>

            <div className="mt-5">
              <Input
                label="Groq Cloud Secret Key"
                defaultValue="gsk_9a7x••••••••••••"
                readOnly
              />
              <div className="mt-3 flex flex-wrap gap-2">
                <Button size="sm" variant="dark">
                  Test Ping
                </Button>
                <Button size="sm" variant="secondary">
                  Update
                </Button>
              </div>
              <p className="mono mt-2 text-[10px] text-[var(--text-muted)]">
                Hardware enclave masked · last 4 only stored in UI
              </p>
            </div>

            <label className="mt-5 block">
              <span className="mono text-[11px] tracking-[0.08em] text-[var(--text-secondary)] uppercase">
                Default Grounding Model
              </span>
              <select className="mt-2 h-11 w-full rounded-[12px] border border-[var(--hairline)] bg-[var(--bg-elevated)] px-3 text-sm outline-none">
                <option>llama-3.3-70b-versatile (Context: 128k)</option>
                <option>llama-3.1-8b-instant</option>
              </select>
            </label>
          </section>

          <section className="rounded-[16px] border border-[var(--hairline)] bg-[var(--surface)] p-5">
            <h2 className="text-base text-[var(--text)]">Synthesis Portability</h2>
            <div className="mt-4 grid gap-3 md:grid-cols-3">
              {[
                { ext: ".JSON", desc: "Complete Graph", meta: "14.2 MB" },
                { ext: ".BIB", desc: "BibTeX Index", meta: "142 citations" },
                { ext: ".PDF", desc: "Archival Folio", meta: "Typeset report" },
              ].map((item) => (
                <div
                  key={item.ext}
                  className="rounded-[12px] border border-[var(--hairline)] bg-[var(--bg-elevated)] p-3"
                >
                  <p className="text-sm text-[var(--text)]">{item.ext}</p>
                  <p className="mt-1 text-xs text-[var(--text-secondary)]">{item.desc}</p>
                  <p className="mono mt-2 text-[10px] text-[var(--text-muted)]">{item.meta}</p>
                </div>
              ))}
            </div>
          </section>
        </div>

        <div className="space-y-5">
          <section className="rounded-[16px] border border-[var(--hairline)] bg-[var(--surface)] p-5">
            <h2 className="text-base text-[var(--text)]">Privacy Guardrails</h2>
            <div className="mt-4 space-y-5">
              <Toggle
                checked={ephemeral}
                onChange={setEphemeral}
                label="Ephemeral RAM Buffer"
                description="Flush source texts after 60 minutes idle."
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
              </div>
              <Toggle
                checked={opfs}
                onChange={setOpfs}
                label="Client-Side OPFS Indexing"
                description="Store document chunks in Origin Private File System."
              />
            </div>
          </section>

          <section className="rounded-[16px] border border-[var(--hairline)] bg-[var(--surface)] p-5">
            <h2 className="text-base text-[var(--text)]">Quiet Ergonomics</h2>
            <div className="mt-4 grid grid-cols-2 gap-2">
              {[
                { id: "dark", label: "Quiet Dark" },
                { id: "light", label: "Quiet Light" },
              ].map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setTheme(item.id)}
                  className={`rounded-[12px] border px-3 py-3 text-sm ${
                    theme === item.id
                      ? "border-[var(--accent)]/40 bg-[var(--accent-soft)] text-[var(--accent)]"
                      : "border-[var(--hairline)] text-[var(--text-secondary)]"
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
                description="Disable ambient motion."
              />
            </div>
            <div className="mt-5 flex items-center justify-between">
              <span className="text-sm">Reading Serif Size</span>
              <div className="flex items-center gap-2">
                <Button size="sm" variant="dark" onClick={() => setFontSize((v) => Math.max(14, v - 1))}>
                  A−
                </Button>
                <span className="mono text-xs text-[var(--text-muted)]">{fontSize}px</span>
                <Button size="sm" variant="dark" onClick={() => setFontSize((v) => Math.min(20, v + 1))}>
                  A+
                </Button>
              </div>
            </div>
          </section>

          <section className="rounded-[16px] border border-[var(--danger)]/30 bg-[var(--danger-soft)] p-5">
            <h2 className="text-base text-[var(--danger)]">Irreversible Operations</h2>
            <p className="mt-2 text-xs text-[var(--text-secondary)]">
              Immediately deletes encrypted session state, embedding cache, and remembered keys.
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
