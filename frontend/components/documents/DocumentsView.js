"use client";

import DocumentList from "@/components/documents/DocumentList";
import Dropzone from "@/components/documents/Dropzone";
import Page from "@/components/layout/Page";
import Alert from "@/components/ui/Alert";
import EmptyState from "@/components/ui/EmptyState";
import { PageLoader } from "@/components/ui/Spinner";
import { useDocuments } from "@/hooks/useDocuments";

function summary(documents) {
  const count = (status) => documents.filter((d) => d.status === status).length;
  const parts = [`${documents.length} document${documents.length === 1 ? "" : "s"}`];
  const indexing = count("uploaded") + count("indexing");
  if (count("indexed")) parts.push(`${count("indexed")} indexed`);
  if (indexing) parts.push(`${indexing} processing`);
  if (count("failed")) parts.push(`${count("failed")} failed`);
  return parts.join(" · ");
}

export default function DocumentsView() {
  const { documents, loading, error, refresh, upload, remove, reindex } = useDocuments();
  const failed = documents.some((d) => d.status === "failed");

  return (
    <Page
      eyebrow="Library"
      title="Documents"
      description="Everything Folio can cite. Answers only use indexed documents."
    >
      <Dropzone onUpload={upload} />

      <div className="mt-10">
        {loading ? (
          <PageLoader label="Loading your documents…" />
        ) : error ? (
          <Alert
            action={
              <button onClick={refresh} className="shrink-0 font-medium underline">
                Retry
              </button>
            }
          >
            {error}
          </Alert>
        ) : documents.length === 0 ? (
          <EmptyState
            title="No documents yet"
            description="Upload a PDF, DOCX, TXT, or Markdown file above to start asking questions about it."
          />
        ) : (
          <div className="space-y-3">
            <div className="flex items-center justify-between gap-4">
              <h2 className="caption-upper text-muted">{summary(documents)}</h2>
              <button onClick={refresh} className="text-sm text-muted hover:text-ink">
                Refresh
              </button>
            </div>
            {failed && (
              <Alert tone="info">
                A failed document couldn&apos;t be read or indexed. Try Reindex, or delete it and upload a cleaner copy.
              </Alert>
            )}
            <DocumentList documents={documents} onRemove={remove} onReindex={reindex} />
          </div>
        )}
      </div>
    </Page>
  );
}
