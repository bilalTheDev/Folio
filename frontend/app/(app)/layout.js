import { Suspense } from "react";
import AuthGuard from "@/components/auth/AuthGuard";
import AppShell from "@/components/layout/AppShell";
import { PageLoader } from "@/components/ui/Spinner";

export default function AppLayout({ children }) {
  return (
    <Suspense fallback={<PageLoader />}>
      <AuthGuard mode="app">
        <AppShell>{children}</AppShell>
      </AuthGuard>
    </Suspense>
  );
}
