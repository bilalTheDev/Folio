export default function Spinner({ className = "size-5" }) {
  return (
    <svg className={`animate-spin ${className}`} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" className="opacity-20" />
      <path d="M22 12a10 10 0 0 0-10-10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

export function PageLoader({ label = "Loading…" }) {
  return (
    <div className="flex flex-1 items-center justify-center gap-3 py-24 text-[15px] text-muted" role="status">
      <Spinner />
      {label}
    </div>
  );
}
