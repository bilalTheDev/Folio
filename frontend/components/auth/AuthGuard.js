"use client";

import { useEffect } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { PageLoader } from "@/components/ui/Spinner";
import { bootstrapSession } from "@/hooks/useAuth";
import { useAuthStore } from "@/lib/authStore";
import { APP_HOME, ONBOARDING_STEPS, nextOnboardingRoute, safeNext, stepIndex } from "@/lib/routes";

function redirectFor(mode, status, user, pathname, next) {
  if (status !== "authenticated" && status !== "anonymous") return null;

  if (mode === "guest") {
    if (status !== "authenticated") return null;
    return user.onboarding_completed ? safeNext(next) || APP_HOME : nextOnboardingRoute(user);
  }

  if (status === "anonymous") return `/signin?next=${encodeURIComponent(pathname)}`;

  if (mode === "app") {
    return user.onboarding_completed ? null : nextOnboardingRoute(user);
  }

  // Onboarding: completed users go to the app; nobody may skip ahead of their first unfinished step.
  if (user.onboarding_completed) return APP_HOME;
  const current = ONBOARDING_STEPS.findIndex((s) => pathname.startsWith(s.href));
  const nextStep = user.onboarding?.next_step;
  // Provider and token are one credential-setup pair once documents exist.
  let allowed = nextStep === "done" ? ONBOARDING_STEPS.length - 1 : stepIndex(nextStep);
  if (nextStep === "provider") allowed = stepIndex("token");
  if (current === -1 || current > allowed) return ONBOARDING_STEPS[Math.max(allowed, 0)].href;
  return null;
}

export default function AuthGuard({ mode, children }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const status = useAuthStore((s) => s.status);
  const user = useAuthStore((s) => s.user);

  useEffect(() => {
    bootstrapSession();
  }, []);

  const target = redirectFor(mode, status, user, pathname, searchParams.get("next"));

  useEffect(() => {
    if (target) router.replace(target);
  }, [target, router]);

  if (status === "idle" || status === "loading" || target) {
    return <PageLoader label={target ? "Redirecting…" : "Loading…"} />;
  }
  return children;
}
