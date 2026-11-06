import { forwardRef } from "react";

const Input = forwardRef(function Input({ className = "", invalid = false, ...props }, ref) {
  return (
    <input
      ref={ref}
      aria-invalid={invalid || undefined}
      className={[
        "block h-11 w-full rounded-lg bg-card px-4 text-base tracking-[0.01em] text-ink ring-1 ring-inset placeholder:text-muted-soft",
        "focus:outline-none focus:ring-2 focus:ring-ink disabled:bg-canvas-soft disabled:text-muted",
        invalid ? "ring-error/40" : "ring-hairline-strong",
        className,
      ].join(" ")}
      {...props}
    />
  );
});

export default Input;

export function Field({ label, htmlFor, error, hint, children }) {
  return (
    <div className="space-y-1.5">
      {label && (
        <label htmlFor={htmlFor} className="block text-sm font-medium text-ink">
          {label}
        </label>
      )}
      {children}
      {error ? (
        <p className="text-sm text-error" role="alert">
          {error}
        </p>
      ) : (
        hint && <p className="text-sm text-muted">{hint}</p>
      )}
    </div>
  );
}
