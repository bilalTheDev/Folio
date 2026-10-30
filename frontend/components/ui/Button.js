export function Button({
  children,
  variant = "primary",
  size = "md",
  className = "",
  type = "button",
  ...props
}) {
  const base =
    "inline-flex items-center justify-center gap-2 rounded-[12px] font-medium transition duration-200 disabled:opacity-50 disabled:pointer-events-none";

  const sizes = {
    sm: "h-9 px-3 text-sm",
    md: "h-11 px-4 text-sm",
    lg: "h-12 px-5 text-[15px]",
  };

  const variants = {
    primary:
      "bg-[var(--accent)] text-[#06140f] hover:bg-[var(--accent-strong)] shadow-[0_0_24px_var(--accent-glow)]",
    secondary:
      "bg-transparent text-[var(--text)] border border-[var(--hairline-strong)] hover:bg-white/5",
    ghost: "bg-transparent text-[var(--text-secondary)] hover:text-[var(--text)] hover:bg-white/5",
    danger:
      "bg-[var(--danger-soft)] text-[var(--danger)] border border-[var(--danger)]/30 hover:bg-[var(--danger)]/20",
    dark: "bg-[var(--surface-2)] text-[var(--text)] border border-[var(--hairline)] hover:border-[var(--hairline-strong)]",
  };

  return (
    <button
      type={type}
      className={`${base} ${sizes[size]} ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
