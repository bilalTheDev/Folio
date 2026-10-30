"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

const ACTIONS = [
  { id: "workspace", label: "Go to Workspace", href: "/app" },
  { id: "library", label: "Open Document Vault", href: "/app/library" },
  { id: "upload", label: "Upload a document", href: "/app/documents/new" },
  { id: "history", label: "Chat history", href: "/app/history" },
  { id: "settings", label: "Account & Settings", href: "/app/settings" },
  { id: "home", label: "Marketing home", href: "/" },
];

export function CommandPalette() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");

  useEffect(() => {
    function onKey(event) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen((value) => !value);
      }
      if (event.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return ACTIONS;
    return ACTIONS.filter((item) => item.label.toLowerCase().includes(q));
  }, [query]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/55 px-4 pt-[15vh]">
      <div
        className="w-full max-w-lg overflow-hidden rounded-xl border border-white/[0.1] bg-[var(--surface)] shadow-[var(--shadow-2xl)]"
        role="dialog"
        aria-label="Command palette"
      >
        <input
          autoFocus
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Jump to documents, settings, history…"
          className="h-12 w-full border-b border-white/[0.08] bg-transparent px-4 text-sm outline-none"
        />
        <ul className="max-h-72 overflow-y-auto p-2">
          {filtered.map((item) => (
            <li key={item.id}>
              <button
                type="button"
                className="flex w-full rounded-lg px-3 py-2.5 text-left text-sm text-[var(--text-secondary)] hover:bg-white/[0.05] hover:text-[var(--text)]"
                onClick={() => {
                  setOpen(false);
                  setQuery("");
                  router.push(item.href);
                }}
              >
                {item.label}
              </button>
            </li>
          ))}
          {!filtered.length ? (
            <li className="px-3 py-4 text-sm text-[var(--text-muted)]">No matches</li>
          ) : null}
        </ul>
        <p className="mono border-t border-white/[0.06] px-4 py-2 text-[10px] text-[var(--text-muted)]">
          Esc to close · Ctrl/Cmd + K
        </p>
      </div>
    </div>
  );
}
