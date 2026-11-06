"use client";

import { useState } from "react";
import StatusBadge from "@/components/documents/StatusBadge";
import { getErrorMessage } from "@/lib/api";
import { formatBytes, formatDate } from "@/lib/format";

function DocumentRow({ doc, onRemove, onReindex, showActions }) {
  const [busy, setBusy] = useState(null);
  const [error, setError] = useState("");

  const run = async (kind, fn) => {
    setBusy(kind);
    setError("");
    try {
      await fn(doc.id);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setBusy(null);
    }
  };

  const processing = doc.status === "uploaded" || doc.status === "indexing";

  return (
    <li className="px-5 py-4">
      <div className="flex items-center gap-4">
        <div className="grid size-8 shrink-0 place-items-center rounded-full bg-strong text-[10px] font-semibold uppercase text-muted">
          {doc.filename.split(".").pop()}
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-ink">{doc.filename}</p>
          <p className="text-xs text-muted">
            {formatBytes(doc.size_bytes)} · {formatDate(doc.uploaded_at)}
            {doc.status === "indexed" && ` · ${doc.chunk_count} chunks`}
          </p>
        </div>
        <StatusBadge status={doc.status} />
        {showActions && (
          <div className="flex shrink-0 items-center gap-1">
            {onReindex && (
              <button
                onClick={() => run("reindex", onReindex)}
                disabled={!!busy || processing}
                className="rounded-full px-2 py-1 text-xs font-medium text-body hover:bg-strong disabled:opacity-40"
              >
                {busy === "reindex" ? "Starting…" : "Reindex"}
              </button>
            )}
            <button
              onClick={() => {
                if (window.confirm(`Delete “${doc.filename}”? Its passages will no longer be used in answers.`)) {
                  run("remove", onRemove);
                }
              }}
              disabled={!!busy}
              className="rounded-full px-2 py-1 text-xs font-medium text-error hover:bg-error/5 disabled:opacity-40"
            >
              {busy === "remove" ? "Deleting…" : "Delete"}
            </button>
          </div>
        )}
      </div>
      {error && <p className="mt-2 text-sm text-error">{error}</p>}
    </li>
  );
}

export default function DocumentList({ documents, onRemove, onReindex, showActions = true }) {
  return (
    <ul className="divide-y divide-hairline rounded-2xl border border-hairline bg-card">
      {documents.map((doc) => (
        <DocumentRow key={doc.id} doc={doc} onRemove={onRemove} onReindex={onReindex} showActions={showActions} />
      ))}
    </ul>
  );
}
