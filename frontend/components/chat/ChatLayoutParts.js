"use client";

import Link from "next/link";
import ModelBadge from "@/components/chat/ModelBadge";
import { useDocuments } from "@/hooks/useDocuments";

export function ChatHeader({ title }) {
  return (
    <div className="flex h-16 shrink-0 items-center gap-3 border-b border-hairline/60 bg-canvas/90 px-6 backdrop-blur-md">
      <Link href="/app/history" className="text-[15px] font-medium text-muted hover:text-ink md:hidden" aria-label="All chats">
        ← Chats
      </Link>
      <h1 className="min-w-0 flex-1 truncate font-display text-xl font-light tracking-tight text-ink">{title}</h1>
      <ModelBadge className="shrink-0" />
    </div>
  );
}

export function ComposerDock({ children }) {
  return (
    <div className="shrink-0 border-t border-hairline/60 bg-canvas/90 px-4 pb-5 pt-4 backdrop-blur-md sm:px-6">
      <div className="mx-auto max-w-3xl">
        {children}
        <p className="mt-3 text-center text-xs text-muted-soft">
          Answers are generated only from your documents. Check the cited sources before relying on them.
        </p>
      </div>
    </div>
  );
}

export function IndexingNotice() {
  const { documents, loading } = useDocuments();
  if (loading) return null;
  const indexed = documents.filter((d) => d.status === "indexed").length;
  const busy = documents.filter((d) => d.status === "uploaded" || d.status === "indexing").length;
  if (indexed > 0) return null;

  let message;
  if (busy > 0) message = `${busy} document${busy === 1 ? " is" : "s are"} still being indexed. Answers will improve once indexing finishes.`;
  else if (documents.length > 0) message = "None of your documents could be indexed. Reindex or upload another file.";
  else message = "You have no documents yet. Upload one so Folio has something to answer from.";

  return (
    <div className="mb-3 flex items-center justify-between gap-3 rounded-2xl border border-hairline bg-card px-4 py-3 text-sm text-body">
      <span>{message}</span>
      <Link href="/app/documents" className="shrink-0 text-[15px] font-medium text-ink underline decoration-hairline-strong underline-offset-4 hover:decoration-ink">
        Documents
      </Link>
    </div>
  );
}
