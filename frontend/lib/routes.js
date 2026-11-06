export const ONBOARDING_STEPS = [
  { key: "upload", label: "Upload documents", href: "/onboarding/upload" },
  { key: "provider", label: "Choose a provider", href: "/onboarding/provider" },
  { key: "token", label: "Connect your key", href: "/onboarding/token" },
];

export const APP_HOME = "/app/chat";

export function stepIndex(key) {
  return ONBOARDING_STEPS.findIndex((s) => s.key === key);
}

export function nextOnboardingRoute(user) {
  if (!user) return "/signin";
  if (user.onboarding_completed) return APP_HOME;
  const next = user.onboarding?.next_step;
  // Token is always reached from the provider step with query params.
  const key = next === "token" ? "provider" : next;
  const step = ONBOARDING_STEPS.find((s) => s.key === key);
  return step ? step.href : "/onboarding/provider";
}

export function tokenRoute(provider, authMode) {
  return `/onboarding/token?provider=${encodeURIComponent(provider)}&auth_mode=${encodeURIComponent(authMode)}`;
}

// Only allow same-site relative paths as a post-signin destination.
export function safeNext(next) {
  if (!next || !next.startsWith("/") || next.startsWith("//")) return null;
  return next;
}
