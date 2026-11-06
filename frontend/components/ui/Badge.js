const TONES = {
  neutral: "bg-strong text-ink",
  info: "bg-strong text-ink",
  success: "bg-success/10 text-success",
  warning: "bg-strong text-ink",
  danger: "bg-error/10 text-error",
};

export default function Badge({ tone = "neutral", children, className = "" }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 caption-upper ${TONES[tone]} ${className}`}
    >
      {children}
    </span>
  );
}
