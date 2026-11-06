"use client";

import { useState } from "react";
import SessionRow from "@/components/history/SessionRow";
import Page from "@/components/layout/Page";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";
import { PageLoader } from "@/components/ui/Spinner";
import { filterSessions, useSessions } from "@/hooks/useSessions";

export default function HistoryView() {
  const { sessions, status, error, load } = useSessions();
  const [query, setQuery] = useState("");
  const visible = filterSessions(sessions, query);

  return (
    <Page
      eyebrow="Conversations"
      title="Chat history"
      description="Every conversation you've had with your documents."
      actions={<Button href="/app/chat">New chat</Button>}
    >
      {(status === "idle" || status === "loading") && <PageLoader label="Loading chats…" />}

      {status === "error" && (
        <Alert
          action={
            <button onClick={load} className="shrink-0 font-medium underline">
              Retry
            </button>
          }
        >
          {error}
        </Alert>
      )}

      {status === "ready" && sessions.length === 0 && (
        <EmptyState
          title="No chats yet"
          description="Ask a question about your documents and the conversation will be saved here."
          action={<Button href="/app/chat">Start a chat</Button>}
        />
      )}

      {status === "ready" && sessions.length > 0 && (
        <div className="space-y-4">
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by title"
            aria-label="Search chats by title"
            className="block h-11 w-full max-w-sm rounded-lg bg-card px-4 text-base tracking-[0.01em] text-ink ring-1 ring-inset ring-hairline-strong placeholder:text-muted-soft focus:outline-none focus:ring-2 focus:ring-ink"
          />
          {visible.length === 0 ? (
            <p className="py-10 text-center text-sm text-muted">No chats match “{query.trim()}”.</p>
          ) : (
            <ul className="divide-y divide-hairline rounded-2xl border border-hairline bg-card">
              {visible.map((session) => (
                <SessionRow key={session.id} session={session} />
              ))}
            </ul>
          )}
        </div>
      )}
    </Page>
  );
}
