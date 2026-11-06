"use client";

import { usePathname } from "next/navigation";
import { ONBOARDING_STEPS } from "@/lib/routes";

export default function StepIndicator() {
  const pathname = usePathname();
  const current = ONBOARDING_STEPS.findIndex((s) => pathname.startsWith(s.href));

  return (
    <ol className="flex items-center gap-3 text-[15px]" aria-label="Onboarding progress">
      {ONBOARDING_STEPS.map((step, i) => {
        const done = i < current;
        const active = i === current;
        return (
          <li key={step.key} className="flex items-center gap-3">
            <span className="flex items-center gap-2" aria-current={active ? "step" : undefined}>
              <span
                className={[
                  "grid size-6 place-items-center rounded-full text-xs font-medium",
                  done && "bg-primary text-on-primary",
                  active && "bg-strong text-ink ring-1 ring-ink",
                  !done && !active && "bg-strong text-muted",
                ]
                  .filter(Boolean)
                  .join(" ")}
              >
                {done ? "✓" : i + 1}
              </span>
              <span
                className={`hidden whitespace-nowrap md:inline ${active ? "font-medium text-ink" : "text-muted"}`}
              >
                {step.label}
              </span>
            </span>
            {i < ONBOARDING_STEPS.length - 1 && <span className="h-px w-6 bg-hairline-strong sm:w-10" />}
          </li>
        );
      })}
    </ol>
  );
}
