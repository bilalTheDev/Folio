"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import SignoutButton from "@/components/auth/SignoutButton";
import ModelBadge from "@/components/chat/ModelBadge";
import Logo from "@/components/ui/Logo";
import ThemeToggle from "@/components/ui/ThemeToggle";

const NAV = [
  { href: "/app/chat", label: "Chat" },
  { href: "/app/history", label: "History" },
  { href: "/app/documents", label: "Documents" },
  { href: "/app/settings", label: "Settings" },
];

export default function AppShell({ children }) {
  const pathname = usePathname();

  return (
    <div className="flex h-dvh flex-col bg-canvas">
      <header className="z-10 shrink-0 border-b border-hairline/60 bg-canvas/90 backdrop-blur-md">
        <div className="flex h-16 items-center gap-8 px-6">
          <Logo href="/app/chat" />
          <nav className="hidden items-center gap-6 text-[15px] font-medium md:flex" aria-label="Main">
            {NAV.map((item) => {
              const active = pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={`transition-colors ${active ? "text-ink" : "text-muted hover:text-ink"}`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
          <nav className="flex items-center gap-1 overflow-x-auto text-[15px] font-medium md:hidden" aria-label="Main">
            {NAV.map((item) => {
              const active = pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={`whitespace-nowrap rounded-full px-3 py-1.5 transition-colors ${
                    active ? "bg-strong text-ink" : "text-muted hover:text-ink"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
          <div className="ml-auto flex items-center gap-1">
            <ModelBadge className="hidden lg:inline-flex" />
            <ThemeToggle />
            <SignoutButton />
          </div>
        </div>
      </header>
      <div className="relative flex min-h-0 flex-1">{children}</div>
    </div>
  );
}
