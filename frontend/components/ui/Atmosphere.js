const PALETTE = {
  mint: "var(--color-mint)",
  peach: "var(--color-peach)",
  lavender: "var(--color-lavender)",
  sky: "var(--color-sky)",
  rose: "var(--color-rose)",
};

const QUIET = [
  { color: "mint", size: 340, left: "-12%", top: "-34%", opacity: 0.4 },
  { color: "peach", size: 260, left: "58%", top: "-18%", opacity: 0.28 },
  { color: "lavender", size: 280, left: "72%", top: "48%", opacity: 0.3 },
];

const AUTH = [
  { color: "mint", size: 420, left: "-10%", top: "-22%", opacity: 0.45 },
  { color: "peach", size: 340, left: "52%", top: "-8%", opacity: 0.38 },
  { color: "lavender", size: 280, left: "78%", top: "42%", opacity: 0.35 },
  { color: "sky", size: 240, left: "12%", top: "58%", opacity: 0.28 },
];

export default function Atmosphere({ className = "", orbs = QUIET }) {
  return (
    <div className={`pointer-events-none absolute inset-0 overflow-hidden dark:opacity-50 ${className}`} aria-hidden="true">
      {orbs.map((orb, i) => (
        <span
          key={i}
          className="absolute rounded-full blur-3xl"
          style={{
            background: PALETTE[orb.color],
            width: orb.size,
            height: orb.size,
            left: orb.left,
            top: orb.top,
            opacity: orb.opacity ?? 0.45,
          }}
        />
      ))}
    </div>
  );
}

export function QuietAtmosphere({ className = "" }) {
  return <Atmosphere className={className} orbs={QUIET} />;
}

export function AuthAtmosphere({ className = "" }) {
  return <Atmosphere className={className} orbs={AUTH} />;
}
