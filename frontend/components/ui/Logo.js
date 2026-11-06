import Link from "next/link";

function Mark({ className = "" }) {
  return (
    <svg
      className={className}
      viewBox="0 0 560 160"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <rect x="26" y="34" width="72" height="92" rx="10" fill="currentColor" />
      <path
        d="M54 46H118L138 66V126Q138 136 128 136H64Q54 136 54 126Z"
        fill="currentColor"
      />
      <path d="M118 46L118 66L138 66Z" className="fill-canvas" />
      <text
        x="176"
        y="106"
        fontFamily="var(--font-inter), Inter, Helvetica Neue, Arial, sans-serif"
        fontWeight="700"
        fontSize="64"
        letterSpacing="-1"
        fill="currentColor"
      >
        folio
      </text>
    </svg>
  );
}

export default function Logo({ href = "/" }) {
  return (
    <Link href={href} aria-label="Folio" className="inline-flex shrink-0 items-center text-ink">
      <Mark className="h-7 w-auto" />
    </Link>
  );
}
