import { Suspense } from "react";
import AuthGuard from "@/components/auth/AuthGuard";
import SignoutButton from "@/components/auth/SignoutButton";
import StepIndicator from "@/components/onboarding/StepIndicator";
import { QuietAtmosphere } from "@/components/ui/Atmosphere";
import Logo from "@/components/ui/Logo";
import ThemeToggle from "@/components/ui/ThemeToggle";
import { PageLoader } from "@/components/ui/Spinner";

export default function OnboardingLayout({ children }) {
  return (
    <div className="relative flex flex-1 flex-col overflow-hidden">
      <QuietAtmosphere />
      <header className="relative z-10 border-b border-hairline/60 bg-canvas/90 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-5xl items-center justify-between gap-6 px-6">
          <Logo href="/onboarding/upload" />
          <Suspense>
            <StepIndicator />
          </Suspense>
          <div className="flex items-center gap-1">
            <ThemeToggle />
            <SignoutButton className="hidden whitespace-nowrap sm:inline" />
          </div>
        </div>
      </header>
      <main className="relative z-10 mx-auto w-full max-w-3xl flex-1 overflow-y-auto px-6 py-16">
        <Suspense fallback={<PageLoader />}>
          <AuthGuard mode="onboarding">{children}</AuthGuard>
        </Suspense>
      </main>
    </div>
  );
}
