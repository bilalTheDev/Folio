import { AppSidebar } from "@/components/portal/AppSidebar";
import { CommandPalette } from "@/components/portal/CommandPalette";
import { QuietBar } from "@/components/portal/QuietBar";

export default function PortalLayout({ children }) {
  return (
    <div className="flex h-screen overflow-hidden bg-[var(--bg)] text-[var(--text)]">
      <div className="hidden h-full md:block">
        <AppSidebar />
      </div>
      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <QuietBar />
        <main className="min-h-0 flex-1 overflow-y-auto">{children}</main>
      </div>
      <CommandPalette />
    </div>
  );
}

