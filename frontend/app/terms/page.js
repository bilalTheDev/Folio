import Link from "next/link";
import { Logo } from "@/components/brand/Logo";

export const metadata = {
  title: "Terms · Folio",
};

export default function TermsPage() {
  return (
    <div className="folio-glow min-h-screen px-5 py-10">
      <div className="mx-auto max-w-2xl">
        <Link href="/">
          <Logo />
        </Link>
        <h1 className="display mt-10 text-4xl">Terms</h1>
        <div className="mt-6 space-y-4 text-sm text-[var(--text-secondary)]">
          <p>
            Folio is provided free for personal and portfolio use. You are responsible for keys and
            usage under your chosen inference provider.
          </p>
          <p>
            Do not upload content you are not allowed to process. Answers are grounded in your
            documents but may still be incomplete; verify critical decisions yourself.
          </p>
        </div>
      </div>
    </div>
  );
}
