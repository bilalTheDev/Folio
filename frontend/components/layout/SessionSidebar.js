"use client";

import { useState } from "react";
import SessionRow from "@/components/history/SessionRow";
import Button from "@/components/ui/Button";
import Spinner from "@/components/ui/Spinner";
import { filterSessions, useSessions } from "@/hooks/useSessions";

export default function SessionSidebar() {
  const { sessions, status, error, load } = useSessions();
  const [query, setQuery] = useState("");
  const visible = filterSessions(sessions, query);

  return (
    <aside className="hidden w-72 shrink-0 flex-col border-r border-hairline/60 bg-canvas md:flex" aria-label="Chats">
      <div className="space-y-3 p-4">
        <Button href="/app/chat" className="w-full">
          New chat
        </Button>
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search chats"
          aria-label="Search chats by title"
          className="block h-11 w-full rounded-lg bg-card px-4 text-[15px] text-ink ring-1 ring-inset ring-hairline-strong placeholder:text-muted-soft focus:outline-none focus:ring-2 focus:ring-ink"
        />
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-2 pb-4">
        {(status === "idle" || status === "loading") && (
          <div className="flex items-center gap-2 px-3 py-6 text-sm text-muted">
            <Spinner className="size-4" /> Loading chats…
          </div>
        )}
        {status === "error" && (
          <div className="px-3 py-6 text-sm text-error">
            <p>{error}</p>
            <button onClick={load} className="mt-1 font-medium underline">
              Retry
            </button>
          </div>
        )}
        {status === "ready" && sessions.length === 0 && (
          <p className="px-3 py-6 text-[15px] leading-relaxed text-muted">No chats yet. Your conversations will appear here.</p>
        )}
        {status === "ready" && sessions.length > 0 && visible.length === 0 && (
          <p className="px-3 py-6 text-[15px] text-muted">No chats match “{query.trim()}”.</p>
        )}
        {visible.length > 0 && (
          <>
            <p className="px-3 pb-2 pt-2 caption-upper text-muted">Recent</p>
            <ul className="space-y-0.5">
              {visible.map((session) => (
                <SessionRow key={session.id} session={session} variant="sidebar" />
              ))}
            </ul>
          </>
        )}
      </div>
    </aside>
  );
}
