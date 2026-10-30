import Link from "next/link";
import { DOCUMENTS } from "@/lib/mock-data";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

export const metadata = {
  title: "Document Vault · Folio",
};

export default function LibraryPage() {
  return (
    <div className="mx-auto max-w-4xl px-5 py-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="display text-3xl">Document Vault</h1>
          <p className="mt-2 text-sm text-[var(--text-secondary)]">
            Indexed dossiers ready for grounded questions.
          </p>
        </div>
        <Link href="/app">
          <Button>+ New document</Button>
        </Link>
      </div>
      <div className="mt-8 space-y-3">
        {DOCUMENTS.map((doc) => (
          <Link
            key={doc.id}
            href="/app"
            className="flex items-center justify-between rounded-[14px] border border-[var(--hairline)] bg-[var(--surface)] px-4 py-4 hover:border-[var(--hairline-strong)]"
          >
            <div>
              <p className="text-sm text-[var(--text)]">{doc.title}</p>
              <p className="mt-1 text-xs text-[var(--text-muted)]">
                {doc.pages} pages · {doc.updated}
              </p>
            </div>
            <Badge tone="accent">Ready</Badge>
          </Link>
        ))}
      </div>
    </div>
  );
}
