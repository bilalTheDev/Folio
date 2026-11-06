"use client";

import { useParams } from "next/navigation";
import { useEffect, useRef } from "react";
import { ChatHeader, ComposerDock, IndexingNotice } from "@/components/chat/ChatLayoutParts";
import Composer from "@/components/chat/Composer";
import MessageBubble, { ThinkingMessage } from "@/components/chat/MessageBubble";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";
import { PageLoader } from "@/components/ui/Spinner";
import { useChat } from "@/hooks/useChat";
import { useSessionsStore } from "@/hooks/useSessions";
import { api } from "@/lib/api";

function useSessionTitle(sessionId) {
  const session = useSessionsStore((s) => s.sessions.find((x) => x.id === sessionId));
  const listStatus = useSessionsStore((s) => s.status);
  const upsert = useSessionsStore((s) => s.upsert);

  // Chats older than the sidebar's page aren't in the store; fetch just this one.
  useEffect(() => {
    if (session || listStatus !== "ready") return;
    api
      .get(`/chat/sessions/${sessionId}`)
      .then(({ data }) => upsert(data))
      .catch(() => {});
  }, [session, listStatus, sessionId, upsert]);

  return session?.title;
}

export default function ChatSession() {
  const { sessionId } = useParams();
  const { messages, status, error, sending, send, retry, reload } = useChat(sessionId);
  const title = useSessionTitle(sessionId);
  const bottomRef = useRef(null);
  const initialScroll = useRef(true);

  useEffect(() => {
    if (status !== "ready") return;
    bottomRef.current?.scrollIntoView({ block: "end", behavior: initialScroll.current ? "auto" : "smooth" });
    initialScroll.current = false;
  }, [messages.length, sending, status]);

  if (status === "missing") {
    return (
      <div className="flex flex-1 items-center justify-center p-6">
        <EmptyState
          title="Chat not found"
          description="It may have been deleted, or the link is wrong."
          action={<Button href="/app/chat">Start a new chat</Button>}
        />
      </div>
    );
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <ChatHeader title={title || "Chat"} />
      <div className="min-h-0 flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl space-y-8 px-4 py-8 sm:px-6">
          {status === "loading" && <PageLoader label="Loading messages…" />}
          {status === "error" && (
            <Alert
              action={
                <button onClick={reload} className="shrink-0 font-medium underline">
                  Retry
                </button>
              }
            >
              {error}
            </Alert>
          )}
          {status === "ready" && messages.length === 0 && !sending && (
            <div className="py-20 text-center">
              <p className="caption-upper text-muted">Conversation</p>
              <h2 className="display-sm mt-3 text-ink">Ask your first question</h2>
              <p className="mx-auto mt-3 max-w-sm text-[15px] leading-relaxed text-body">
                Folio will search your documents and cite the passages behind the answer.
              </p>
            </div>
          )}
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} onRetry={retry} />
          ))}
          {sending && <ThinkingMessage />}
          <div ref={bottomRef} />
        </div>
      </div>
      <ComposerDock>
        <IndexingNotice />
        <Composer onSend={send} busy={sending} disabled={status !== "ready"} autoFocus />
      </ComposerDock>
    </div>
  );
}
