import Link from "next/link";
import { WorkspaceShell } from "@/components/workspace/WorkspaceShell";
import { Button } from "@/components/ui/Button";

export const metadata = {
  title: "Try Folio",
};

export default function TryPage() {
  return (
    <div className="min-h-screen bg-[var(--bg)]">
      <div className="flex items-center justify-between border-b border-white/[0.06] px-5 py-3">
        <p className="text-sm text-[var(--text-secondary)]">
          Trial workspace · sample document · sign up to upload your own
        </p>
        <div className="flex gap-2">
          <Link href="/login">
            <Button size="sm">Sign up</Button>
          </Link>
          <Link href="/">
            <Button size="sm" variant="ghost">
              Home
            </Button>
          </Link>
        </div>
      </div>
      <WorkspaceShell compactChrome />
    </div>
  );
}
