export default function ProgressBar({ value, className = "" }) {
  return (
    <div
      className={`h-1.5 w-full overflow-hidden rounded-full bg-strong ${className}`}
      role="progressbar"
      aria-valuenow={value}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div className="h-full rounded-full bg-primary transition-[width]" style={{ width: `${value}%` }} />
    </div>
  );
}
