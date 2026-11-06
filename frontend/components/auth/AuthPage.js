import { Suspense } from "react";
import AuthForm from "@/components/auth/AuthForm";
import AuthGuard from "@/components/auth/AuthGuard";
import { AuthAtmosphere } from "@/components/ui/Atmosphere";
import Logo from "@/components/ui/Logo";
import ThemeToggle from "@/components/ui/ThemeToggle";
import { PageLoader } from "@/components/ui/Spinner";

export default function AuthPage({ mode }) {
  return (
    <main className="relative flex flex-1 flex-col overflow-hidden">
      <AuthAtmosphere />
      <header className="relative z-10 flex h-16 items-center justify-between px-6">
        <Logo />
        <ThemeToggle />
      </header>
      <div className="relative z-10 flex flex-1 items-center justify-center px-6 py-16">
        <div className="w-full max-w-md rounded-2xl border border-hairline bg-card p-8 shadow-soft sm:p-10">
          <Suspense fallback={<PageLoader />}>
            <AuthGuard mode="guest">
              <AuthForm mode={mode} />
            </AuthGuard>
          </Suspense>
        </div>
      </div>
    </main>
  );
}
