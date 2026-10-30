import Link from "next/link";
import { Logo } from "@/components/brand/Logo";

export const metadata = {
  title: "Privacy · Folio",
};

export default function PrivacyPage() {
  return (
    <div className="folio-glow min-h-screen px-5 py-10">
      <div className="mx-auto max-w-2xl">
        <Link href="/">
          <Logo />
        </Link>
        <h1 className="display mt-10 text-4xl">Privacy</h1>
        <div className="mt-6 space-y-4 text-sm text-[var(--text-secondary)]">
          <p>
            Folio stores account identity, extracted text chunks, embeddings, chat messages, citations,
            and optionally an encrypted provider key.
          </p>
          <p>
            Folio does not permanently store original uploaded files. Questions and document text are
            sent to the inference provider you choose; that provider’s data policy also applies.
          </p>
          <p>No third-party advertising or tracking cookies are used.</p>
        </div>
      </div>
    </div>
  );
}
