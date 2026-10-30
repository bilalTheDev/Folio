export function QuietBar() {
  return (
    <div className="flex h-12 items-center justify-between border-b border-[var(--hairline)] px-6">
      <div className="mono flex items-center gap-2 text-[11px] tracking-[0.12em] text-[var(--text-secondary)] uppercase">
        <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent)] shadow-[0_0_8px_var(--accent)]" />
        Quiet session
      </div>
      <div
        className="flex h-8 w-8 items-center justify-center rounded-full border border-[var(--hairline)] bg-[var(--surface)] text-xs text-[var(--text-secondary)]"
        aria-hidden
      >
        CV
      </div>
    </div>
  );
}
