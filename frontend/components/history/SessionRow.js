"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { useSessionsStore } from "@/hooks/useSessions";
import { getErrorMessage } from "@/lib/api";
import { formatRelative, plainPreview } from "@/lib/format";

function IconButton({ label, onClick, disabled, danger, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      title={label}
      className={`grid size-7 place-items-center rounded-full text-muted-soft transition-colors disabled:opacity-40 ${
        danger ? "hover:bg-error/5 hover:text-error" : "hover:bg-strong hover:text-ink"
      }`}
    >
      {children}
    </button>
  );
}

function RenameForm({ initial, onSave, onCancel }) {
  const [value, setValue] = useState(initial);
  const [saving, setSaving] = useState(false);
  // Enter, Escape, and the blur that follows them must settle the edit only once.
  const settled = useRef(false);

  const cancel = () => {
    settled.current = true;
    onCancel();
  };

  const submit = async (e) => {
    e?.preventDefault();
    if (settled.current) return;
    const title = value.trim();
    if (!title || title === initial) return cancel();
    settled.current = true;
    setSaving(true);
    const ok = await onSave(title);
    if (!ok) {
      settled.current = false;
      setSaving(false);
    }
  };

  return (
    <form onSubmit={submit} className="flex flex-1 items-center gap-1">
      <input
        autoFocus
        value={value}
        maxLength={120}
        disabled={saving}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => e.key === "Escape" && cancel()}
        onBlur={submit}
        aria-label="Chat title"
        className="h-8 min-w-0 flex-1 rounded-lg bg-card px-2 text-sm ring-1 ring-inset ring-ink focus:outline-none"
      />
    </form>
  );
}

export default function SessionRow({ session, variant = "list" }) {
  const router = useRouter();
  const pathname = usePathname();
  const rename = useSessionsStore((s) => s.rename);
  const remove = useSessionsStore((s) => s.remove);
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const href = `/app/chat/${session.id}`;
  const active = pathname === href;
  const compact = variant === "sidebar";

  const handleRename = async (title) => {
    setError("");
    try {
      await rename(session.id, title);
      setEditing(false);
      return true;
    } catch (err) {
      setError(getErrorMessage(err, "Couldn't rename this chat."));
      return false;
    }
  };

  const handleDelete = async () => {
    if (!window.confirm(`Delete “${session.title}”? Its messages will be removed permanently.`)) return;
    setBusy(true);
    setError("");
    try {
      await remove(session.id);
      if (active) router.replace("/app/chat");
    } catch (err) {
      setError(getErrorMessage(err, "Couldn't delete this chat."));
      setBusy(false);
    }
  };

  const actions = !editing && (
    <div className={`flex shrink-0 items-center ${compact ? "opacity-0 group-hover:opacity-100 group-focus-within:opacity-100" : ""}`}>
      <IconButton label="Rename chat" onClick={() => setEditing(true)} disabled={busy}>
        <svg className="size-3.5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
          <path d="M13.586 3.586a2 2 0 1 1 2.828 2.828l-.793.793-2.828-2.828.793-.793ZM11.379 5.793 3 14.172V17h2.828l8.38-8.379-2.83-2.828Z" />
        </svg>
      </IconButton>
      <IconButton label="Delete chat" onClick={handleDelete} disabled={busy} danger>
        <svg className="size-3.5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
          <path
            fillRule="evenodd"
            d="M8.75 1A2.75 2.75 0 0 0 6 3.75v.443c-.795.077-1.584.176-2.365.298a.75.75 0 1 0 .23 1.482l.149-.022.841 10.518A2.75 2.75 0 0 0 7.596 19h4.807a2.75 2.75 0 0 0 2.742-2.53l.841-10.52.149.023a.75.75 0 0 0 .23-1.482A41.03 41.03 0 0 0 14 4.193V3.75A2.75 2.75 0 0 0 11.25 1h-2.5ZM10 4c.84 0 1.673.025 2.5.075V3.75c0-.69-.56-1.25-1.25-1.25h-2.5c-.69 0-1.25.56-1.25 1.25v.325C8.327 4.025 9.16 4 10 4ZM8.58 7.72a.75.75 0 0 0-1.5.06l.3 7.5a.75.75 0 1 0 1.5-.06l-.3-7.5Zm4.34.06a.75.75 0 1 0-1.5-.06l-.3 7.5a.75.75 0 1 0 1.5.06l.3-7.5Z"
            clipRule="evenodd"
          />
        </svg>
      </IconButton>
    </div>
  );

  if (compact) {
    return (
      <li>
        <div
          className={`group flex items-center gap-1 rounded-xl pr-1 transition-colors ${
            active ? "bg-strong" : "hover:bg-card"
          }`}
        >
          {editing ? (
            <div className="flex-1 p-1">
              <RenameForm initial={session.title} onSave={handleRename} onCancel={() => setEditing(false)} />
            </div>
          ) : (
            <Link href={href} aria-current={active ? "page" : undefined} className="min-w-0 flex-1 px-3 py-2">
              <span className={`block truncate text-sm ${active ? "font-medium text-ink" : "text-body"}`}>
                {session.title}
              </span>
              <span className="block text-xs text-muted-soft">{formatRelative(session.updated_at)}</span>
            </Link>
          )}
          {actions}
        </div>
        {error && <p className="px-3 pb-1 text-xs text-error">{error}</p>}
      </li>
    );
  }

  return (
    <li className="px-5 py-4">
      <div className="flex items-start gap-4">
        {editing ? (
          <RenameForm initial={session.title} onSave={handleRename} onCancel={() => setEditing(false)} />
        ) : (
          <Link href={href} className="group min-w-0 flex-1">
            <div className="flex items-baseline justify-between gap-4">
              <p className="truncate text-sm font-medium text-ink group-hover:underline">{session.title}</p>
              <span className="shrink-0 text-xs text-muted-soft">{formatRelative(session.updated_at)}</span>
            </div>
            <p className="mt-0.5 line-clamp-2 text-sm text-muted">
              {plainPreview(session.last_message) || <span className="italic text-muted-soft">No messages yet</span>}
            </p>
          </Link>
        )}
        {actions}
      </div>
      {error && <p className="mt-2 text-sm text-error">{error}</p>}
    </li>
  );
}
