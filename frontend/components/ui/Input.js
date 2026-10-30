export function Input({ label, hint, className = "", ...props }) {
  return (
    <label className={`block ${className}`}>
      {label ? (
        <span className="mono mb-2 flex items-center justify-between text-[11px] tracking-[0.14em] text-[var(--text-secondary)] uppercase">
          <span>{label}</span>
          {hint}
        </span>
      ) : null}
      <input
        className="h-11 w-full rounded-lg border border-white/[0.08] bg-[var(--bg-chrome)] px-3 text-sm text-[var(--text)] placeholder:text-[var(--text-muted)] outline-none transition focus:border-[var(--accent)]/40"
        {...props}
      />
    </label>
  );
}
