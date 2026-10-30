export function Input({ label, hint, className = "", ...props }) {
  return (
    <label className={`block ${className}`}>
      {label ? (
        <span className="mono mb-2 flex items-center justify-between text-[11px] tracking-[0.08em] text-[var(--text-secondary)] uppercase">
          <span>{label}</span>
          {hint}
        </span>
      ) : null}
      <input
        className="h-11 w-full rounded-[12px] border border-[var(--hairline)] bg-[var(--bg-elevated)] px-3 text-sm text-[var(--text)] placeholder:text-[var(--text-muted)] outline-none transition focus:border-[var(--accent)]/50"
        {...props}
      />
    </label>
  );
}
