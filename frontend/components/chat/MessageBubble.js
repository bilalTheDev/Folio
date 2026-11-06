"use client";

import Link from "next/link";
import { useState } from "react";
import CitationChip from "@/components/chat/CitationChip";
import MessageContent from "@/components/chat/MessageContent";
import SourcePanel from "@/components/chat/SourcePanel";
import Spinner from "@/components/ui/Spinner";

const SETTINGS_ERRORS = new Set([
  "missing_token",
  "missing_provider",
  "token_unreadable",
  "provider_auth",
  "provider_model_unavailable",
]);

function Avatar() {
  return (
    <span className="grid size-8 shrink-0 place-items-center rounded-full bg-strong text-xs font-medium text-ink">
      F
    </span>
  );
}

function AssistantMessage({ message }) {
  const [open, setOpen] = useState(null);
  const sources = message.sources || [];
  const toggle = (i) => setOpen((current) => (current === i ? null : i));

  return (
    <div className="flex gap-3">
      <Avatar />
      <div className="min-w-0 flex-1 pt-0.5">
        <MessageContent content={message.content} sourceCount={sources.length} activeSource={open} onCite={toggle} />
        {message.groundedness_warning && (
          <p className="mt-3 text-xs text-muted">This answer may not be fully grounded in your documents.</p>
        )}
        {sources.length > 0 && (
          <div className="mt-4">
            <p className="mb-2 caption-upper text-muted">Sources · select one to verify the passage</p>
            <div className="flex flex-wrap gap-2">
              {sources.map((source, i) => (
                <CitationChip key={i} index={i} source={source} active={open === i} onClick={() => toggle(i)} />
              ))}
            </div>
            {open !== null && sources[open] && (
              <SourcePanel index={open} source={sources[open]} onClose={() => setOpen(null)} />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function UserMessage({ message, onRetry }) {
  return (
    <div className="flex flex-col items-end">
      <div
        className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-[15px] leading-relaxed ${
          message.failed ? "bg-strong text-muted" : "bg-primary text-on-primary"
        }`}
      >
        {message.content}
      </div>
      {message.failed && (
        <div className="mt-2 max-w-[85%] text-right text-sm text-error" role="alert">
          <p>{message.error}</p>
          <div className="mt-1 flex justify-end gap-3 font-medium">
            {SETTINGS_ERRORS.has(message.errorCode) && (
              <Link href="/app/settings" className="text-body underline hover:text-ink">
                Open settings
              </Link>
            )}
            <button onClick={() => onRetry(message)} className="underline hover:text-ink">
              Retry
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export function ThinkingMessage() {
  return (
    <div className="flex gap-3" role="status">
      <Avatar />
      <div className="flex items-center gap-2 pt-1 text-sm text-muted">
        <Spinner className="size-4" />
        Searching your documents and drafting an answer…
      </div>
    </div>
  );
}

export default function MessageBubble({ message, onRetry }) {
  return message.role === "assistant" ? (
    <AssistantMessage message={message} />
  ) : (
    <UserMessage message={message} onRetry={onRetry} />
  );
}
