"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Logo } from "@/components/brand/Logo";

const LINKS = [
  { href: "/app", label: "Workspace", match: (p) => p === "/app" || p.startsWith("/app/threads") },
  { href: "/app/settings", label: "Account & Settings", match: (p) => p.startsWith("/app/settings") },
  { href: "/app/admin", label: "Admin Portal", match: (p) => p.startsWith("/app/admin") },
  { href: "/app/library", label: "Document Vault", match: (p) => p.startsWith("/app/library") },
];

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-full w-[240px] shrink-0 flex-col border-r border-[var(--hairline)] bg-[var(--bg-elevated)]">
      <div className="flex items-center gap-2 px-5 pt-5 pb-6">
        <Logo size={26} />
        <span className="mono rounded-full border border-[var(--hairline)] px-2 py-0.5 text-[10px] tracking-wider text-[var(--text-muted)]">
          PORTAL
        </span>
      </div>

      <nav className="flex flex-1 flex-col gap-1 px-3">
        {LINKS.map((link) => {
          const active = link.match(pathname);
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`rounded-[12px] px-3 py-2.5 text-sm transition ${
                active
                  ? "bg-[var(--accent-soft)] text-[var(--accent)]"
                  : "text-[var(--text-secondary)] hover:bg-white/5 hover:text-[var(--text)]"
              }`}
            >
              {link.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-[var(--hairline)] p-4">
        <div className="flex items-center justify-between gap-2">
          <div>
            <p className="text-sm text-[var(--text)]">C. Vance</p>
            <p className="text-xs text-[var(--text-muted)]">Reader</p>
          </div>
          <Link
            href="/sign-in"
            className="rounded-lg border border-[var(--hairline)] px-2 py-1 text-xs text-[var(--text-secondary)] hover:text-[var(--text)]"
          >
            Log out
          </Link>
        </div>
      </div>
    </aside>
  );
}
