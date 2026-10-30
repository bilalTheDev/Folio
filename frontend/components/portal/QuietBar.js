export function QuietBar({ context = "SESSION #4081-V" }) {
  return (
    <div className="flex h-12 shrink-0 items-center justify-between border-b border-white/[0.06] bg-[var(--bg)] px-6">
      <p className="mono text-[10px] tracking-[0.16em] text-[var(--text-muted)] uppercase">
        {context}
      </p>
      <div className="flex items-center gap-4">
        <div className="mono flex items-center gap-2 text-[11px] tracking-[0.12em] text-[var(--text-secondary)] uppercase">
          <span className="live-dot h-1.5 w-1.5 rounded-full bg-[var(--accent)] shadow-[0_0_8px_var(--accent)]" />
          Quiet session · Live
        </div>
        <div
          className="flex h-8 w-8 items-center justify-center rounded-full border border-white/[0.08] bg-[var(--surface)] text-xs text-[var(--text-secondary)]"
          aria-hidden
        >
          CV
        </div>
      </div>
    </div>
  );
}
