export function Logo({ withWordmark = true, size = 28 }) {
  return (
    <span className="inline-flex items-center gap-2.5">
      <span
        className="inline-flex items-center justify-center rounded-full"
        style={{
          width: size,
          height: size,
          background: "linear-gradient(135deg, #8b7cff, #3ddc97)",
        }}
        aria-hidden
      >
        <svg width={size * 0.55} height={size * 0.55} viewBox="0 0 24 24" fill="none">
          <path
            d="M6 4h9a3 3 0 0 1 3 3v13l-4.5-2.2L9 20V7a1 1 0 0 0-1-1H6V4z"
            fill="white"
            fillOpacity="0.95"
          />
        </svg>
      </span>
      {withWordmark ? (
        <span className="display text-[1.15rem] tracking-tight text-[var(--text)]">Folio</span>
      ) : null}
    </span>
  );
}
