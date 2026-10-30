export function Badge({ children, tone = "neutral", className = "" }) {
  const tones = {
    neutral: "bg-white/[0.04] text-[var(--text-secondary)] border-white/[0.08]",
    accent: "bg-[var(--accent-soft)] text-[var(--accent)] border-[var(--accent)]/25",
    cyan: "bg-[rgba(56,189,248,0.12)] text-[var(--cyan)] border-[var(--cyan)]/25",
    violet: "bg-[rgba(167,139,250,0.12)] text-[var(--violet-muted)] border-[var(--violet-muted)]/25",
    danger: "bg-[var(--danger-soft)] text-[var(--danger)] border-[var(--danger)]/25",
    warning: "bg-[rgba(245,158,11,0.12)] text-[#f59e0b] border-[#f59e0b]/25",
  };

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[11px] font-medium ${tones[tone]} ${className}`}
    >
      {children}
    </span>
  );
}
