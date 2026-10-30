export function Button({
  children,
  variant = "primary",
  size = "md",
  className = "",
  type = "button",
  ...props
}) {
  const base =
    "inline-flex items-center justify-center gap-2 font-medium transition-all duration-200 disabled:pointer-events-none disabled:opacity-45";

  const sizes = {
    sm: "h-8 px-3 text-sm rounded-md",
    md: "h-10 px-4 text-sm rounded-lg",
    lg: "h-11 px-5 text-[15px] rounded-lg",
    pill: "h-9 px-4 text-sm rounded-full",
    icon: "h-10 w-10 rounded-full",
  };

  const variants = {
    primary:
      "bg-[var(--accent)] text-[var(--accent-ink)] hover:bg-[var(--accent-hover)]",
    secondary:
      "bg-transparent text-[var(--text)] border border-white/[0.12] hover:bg-white/[0.04]",
    ghost:
      "bg-transparent text-[var(--text-secondary)] hover:text-[var(--text)] hover:bg-white/[0.04]",
    dark:
      "bg-[var(--surface-elevated)] text-[var(--text)] border border-white/[0.08] hover:border-white/[0.14]",
    danger:
      "bg-[var(--danger-soft)] text-[var(--danger)] border border-[var(--danger)]/30 hover:bg-[var(--danger)]/20",
  };

  return (
    <button
      type={type}
      className={`${base} ${sizes[size] || sizes.md} ${variants[variant] || variants.primary} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
