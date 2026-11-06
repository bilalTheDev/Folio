"use client";

import { useEffect, useId, useRef, useState } from "react";
import Spinner from "@/components/ui/Spinner";

const MAX_LENGTH = 4000;

export default function Composer({ onSend, disabled = false, busy = false, placeholder = "Ask about your documents…", autoFocus = false }) {
  const [value, setValue] = useState("");
  const ref = useRef(null);
  // Hidden routes stay mounted, so several composers can coexist in the DOM.
  const id = useId();

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [value]);

  useEffect(() => {
    if (autoFocus) ref.current?.focus();
  }, [autoFocus]);

  const trimmed = value.trim();
  const tooLong = value.length > MAX_LENGTH;
  const canSend = !!trimmed && !tooLong && !disabled && !busy;

  const submit = (e) => {
    e?.preventDefault();
    if (!canSend) return;
    onSend(trimmed);
    setValue("");
  };

  return (
    <form onSubmit={submit} className="rounded-2xl border border-hairline bg-card p-3 shadow-soft focus-within:border-ink focus-within:ring-2 focus-within:ring-ink/10">
      <label htmlFor={id} className="sr-only">
        Message
      </label>
      <textarea
        id={id}
        ref={ref}
        rows={1}
        value={value}
        disabled={disabled}
        placeholder={placeholder}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) submit(e);
        }}
        className="block max-h-[200px] w-full resize-none bg-transparent px-3 py-2 text-base leading-relaxed tracking-[0.01em] text-ink placeholder:text-muted-soft focus:outline-none disabled:text-muted-soft"
      />
      <div className="flex items-center justify-between gap-3 px-2 pt-2">
        <span className={`text-xs ${tooLong ? "text-error" : "text-muted-soft"}`}>
          {value.length > MAX_LENGTH * 0.8 ? `${value.length}/${MAX_LENGTH}` : "Enter to send · Shift+Enter for a new line"}
        </span>
        <button
          type="submit"
          disabled={!canSend}
          aria-label="Send message"
          className="grid size-10 place-items-center rounded-full bg-primary text-on-primary transition-colors hover:bg-primary-active disabled:bg-strong disabled:text-muted-soft"
        >
          {busy ? (
            <Spinner className="size-4" />
          ) : (
            <svg className="size-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path d="M3.105 2.288a.75.75 0 0 0-.826.95l1.414 4.926A1.5 1.5 0 0 0 5.135 9.25h6.115a.75.75 0 0 1 0 1.5H5.135a1.5 1.5 0 0 0-1.442 1.086l-1.414 4.926a.75.75 0 0 0 .826.95 28.897 28.897 0 0 0 15.293-7.155.75.75 0 0 0 0-1.114A28.897 28.897 0 0 0 3.105 2.288Z" />
            </svg>
          )}
        </button>
      </div>
    </form>
  );
}
