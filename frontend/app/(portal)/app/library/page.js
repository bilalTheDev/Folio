"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { DOCUMENTS } from "@/lib/mock-data";
import { listDocuments } from "@/lib/api/documents";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

function formatUpdated(value) {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return String(value);
  }
}

export default function LibraryPage() {
  const [docs, setDocs] = useState([]);
  const [source, setSource] = useState("loading");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await listDocuments();
        if (!cancelled) {
          setDocs(
            (data.items || []).map((item) => ({
              id: item.id,
              title: item.title,
              pages: item.page_count,
              updated: formatUpdated(item.created_at),
              status: item.status,
            })),
          );
          setSource("api");
        }
        return;
      } catch {
        // fall through to mock
      }
      if (!cancelled) {
        setDocs(
          DOCUMENTS.map((item) => ({
            id: item.id,
            title: item.title,
            pages: item.pages,
            updated: item.updated,
            status: "ready",
          })),
        );
        setSource("demo");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="mx-auto max-w-4xl px-5 py-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="display text-3xl">Document Vault</h1>
          <p className="mt-2 text-sm text-[var(--text-secondary)]">
            Indexed dossiers ready for grounded questions.
            {source === "demo" ? " Showing demo documents until you sign in." : null}
          </p>
        </div>
        <Link href="/app/documents/new">
          <Button>+ New document</Button>
        </Link>
      </div>
      <div className="mt-8 space-y-3">
        {source === "loading" ? (
          <p className="text-sm text-[var(--text-muted)]">Loading documents…</p>
        ) : null}
        {docs.map((doc) => (
          <Link
            key={doc.id}
            href="/app"
            className="flex items-center justify-between rounded-xl border border-white/[0.07] bg-[var(--surface)] px-4 py-4 transition hover:border-white/[0.12]"
          >
            <div>
              <p className="text-sm text-[var(--text)]">{doc.title}</p>
              <p className="mt-1 text-xs text-[var(--text-muted)]">
                {doc.pages} pages · {doc.updated}
              </p>
            </div>
            <Badge tone={doc.status === "ready" ? "accent" : "neutral"}>
              {doc.status === "ready" ? "Ready" : doc.status || "Ready"}
            </Badge>
          </Link>
        ))}
        {source !== "loading" && !docs.length ? (
          <div className="rounded-xl border border-dashed border-white/[0.12] px-6 py-10 text-center">
            <p className="text-sm text-[var(--text-secondary)]">No documents yet.</p>
            <Link href="/app/documents/new" className="mt-4 inline-block">
              <Button size="sm">Upload your first file</Button>
            </Link>
          </div>
        ) : null}
      </div>
    </div>
  );
}
