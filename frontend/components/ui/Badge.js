export function Badge({ children, tone = "neutral", className = "" }) {
  const tones = {
    neutral: "bg-white/5 text-[var(--text-secondary)] border-white/10",
    accent: "bg-[var(--accent-soft)] text-[var(--accent)] border-[var(--accent)]/25",
    violet: "bg-[var(--violet-soft)] text-[#c4b5fd] border-[var(--violet)]/30",
    danger: "bg-[var(--danger-soft)] text-[var(--danger)] border-[var(--danger)]/25",
    warning: "bg-[rgba(245,185,78,0.12)] text-[var(--warning)] border-[var(--warning)]/25",
  };

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[11px] font-medium ${tones[tone]} ${className}`}
    >
      {children}
    </span>
  );
}
