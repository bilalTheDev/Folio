const TONES = {
  error: "bg-error/5 text-error ring-error/15",
  success: "bg-success/5 text-success ring-success/15",
  info: "bg-strong text-body ring-hairline",
};

export default function Alert({ tone = "error", children, action, className = "" }) {
  if (!children) return null;
  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={`flex items-start justify-between gap-3 rounded-xl px-4 py-3 text-sm ring-1 ring-inset ${TONES[tone]} ${className}`}
    >
      <div>{children}</div>
      {action}
    </div>
  );
}
