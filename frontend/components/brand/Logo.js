export function Logo({ withWordmark = true, size = 28 }) {
  return (
    <span className="inline-flex items-center gap-2.5">
      <span
        className="inline-flex items-center justify-center rounded-full bg-[var(--accent)]"
        style={{ width: size, height: size }}
        aria-hidden
      >
        <svg
          width={size * 0.52}
          height={size * 0.52}
          viewBox="0 0 24 24"
          fill="none"
        >
          <path
            d="M7 4.5h8.2A2.8 2.8 0 0 1 18 7.3v12.2l-3.8-1.7-3.8 1.7V7.2A1.2 1.2 0 0 0 9.2 6H7V4.5Z"
            fill="#061B14"
          />
        </svg>
      </span>
      {withWordmark ? (
        <span className="display text-[1.2rem] tracking-tight text-[var(--text)]">
          Folio
        </span>
      ) : null}
    </span>
  );
}
