import { AppSidebar } from "@/components/portal/AppSidebar";
import { QuietBar } from "@/components/portal/QuietBar";

export default function PortalLayout({ children }) {
  return (
    <div className="flex min-h-screen bg-[var(--bg)]">
      <div className="sticky top-0 hidden h-screen md:block">
        <AppSidebar />
      </div>
      <div className="flex min-w-0 flex-1 flex-col">
        <QuietBar />
        <main className="flex-1">{children}</main>
      </div>
    </div>
  );
}
