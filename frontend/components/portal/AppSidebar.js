"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Logo } from "@/components/brand/Logo";
import {
  IconArchive,
  IconFileText,
  IconSettings,
  IconShield,
} from "@/components/icons/NavIcons";

const LINKS = [
  {
    href: "/app",
    label: "Workspace",
    icon: IconFileText,
    match: (p) => p === "/app" || p.startsWith("/app/threads") || p === "/workspace",
  },
  {
    href: "/app/library",
    label: "Document Vault",
    icon: IconArchive,
    match: (p) => p.startsWith("/app/library") || p.startsWith("/app/documents"),
  },
  {
    href: "/app/history",
    label: "History",
    icon: IconFileText,
    match: (p) => p.startsWith("/app/history"),
  },
  {
    href: "/app/settings",
    label: "Account & Settings",
    icon: IconSettings,
    match: (p) => p.startsWith("/app/settings") || p === "/settings",
  },
  {
    href: "/app/admin",
    label: "Admin Portal",
    icon: IconShield,
    match: (p) => p.startsWith("/app/admin") || p === "/admin",
  },
];

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-full w-64 shrink-0 flex-col justify-between border-r border-white/[0.06] bg-[var(--bg-chrome)] p-4">
      <div>
        <div className="mb-6 flex items-center gap-2 px-1 pt-1">
          <Logo size={24} />
          <span className="mono rounded-full border border-white/[0.08] px-2 py-0.5 text-[10px] tracking-[0.14em] text-[var(--text-muted)]">
            PORTAL
          </span>
        </div>

        <nav className="flex flex-col gap-1">
          {LINKS.map((link) => {
            const active = link.match(pathname);
            const Icon = link.icon;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm transition ${
                  active
                    ? "border-l-2 border-[var(--accent)] bg-white/[0.05] pl-[10px] text-[var(--text)]"
                    : "border-l-2 border-transparent text-[var(--text-secondary)] hover:bg-white/[0.03] hover:text-[var(--text)]"
                }`}
              >
                <Icon className="h-4 w-4 shrink-0 opacity-80" />
                {link.label}
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="rounded-lg border border-white/[0.06] bg-[var(--surface)] px-3 py-3">
        <div className="flex items-center justify-between gap-2">
          <div>
            <p className="text-sm text-[var(--text)]">C. Vance</p>
            <p className="text-xs text-[var(--text-muted)]">Reader</p>
          </div>
          <Link
            href="/login"
            className="rounded-md border border-white/[0.08] px-2 py-1 text-[11px] text-[var(--text-secondary)] hover:text-[var(--text)]"
          >
            Log out
          </Link>
        </div>
      </div>
    </aside>
  );
}
