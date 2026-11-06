import Link from "next/link";
import Spinner from "./Spinner";

const VARIANTS = {
  primary: "bg-primary text-on-primary hover:bg-primary-active disabled:bg-muted-soft disabled:text-on-primary/70",
  secondary: "bg-transparent text-ink ring-1 ring-inset ring-hairline-strong hover:bg-strong disabled:text-muted-soft",
  ghost: "text-ink hover:bg-strong disabled:text-muted-soft",
  danger: "bg-transparent text-error ring-1 ring-inset ring-error/20 hover:bg-error/5 disabled:text-error/40",
};

const SIZES = {
  sm: "h-8 px-4 text-[13px] gap-1.5",
  md: "h-10 px-5 text-[15px] gap-2",
  lg: "h-11 px-6 text-[15px] gap-2",
};

export function buttonClasses({ variant = "primary", size = "md", className = "" } = {}) {
  return [
    "inline-flex items-center justify-center rounded-full font-medium leading-none transition-colors",
    "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink",
    "disabled:cursor-not-allowed",
    VARIANTS[variant],
    SIZES[size],
    className,
  ].join(" ");
}

export default function Button({
  variant = "primary",
  size = "md",
  loading = false,
  disabled,
  className = "",
  href,
  children,
  ...props
}) {
  const classes = buttonClasses({ variant, size, className });
  if (href) {
    return (
      <Link href={href} className={classes} {...props}>
        {children}
      </Link>
    );
  }
  return (
    <button className={classes} disabled={disabled || loading} {...props}>
      {loading && <Spinner className="size-4" />}
      {children}
    </button>
  );
}
