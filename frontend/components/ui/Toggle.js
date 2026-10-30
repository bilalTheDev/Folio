"use client";

export function Toggle({ checked, onChange, label, description }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className="flex w-full items-start justify-between gap-4 text-left"
    >
      <span>
        <span className="block text-sm text-[var(--text)]">{label}</span>
        {description ? (
          <span className="mt-1 block text-xs leading-relaxed text-[var(--text-muted)]">
            {description}
          </span>
        ) : null}
      </span>
      <span
        className={`relative mt-0.5 h-6 w-11 shrink-0 rounded-full transition-colors duration-200 ${
          checked ? "bg-[var(--accent)]" : "bg-white/15"
        }`}
      >
        <span
          className={`absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white transition-transform duration-200 ${
            checked ? "translate-x-5" : ""
          }`}
        />
      </span>
    </button>
  );
}
