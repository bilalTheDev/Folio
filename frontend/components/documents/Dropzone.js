"use client";

import { useRef, useState } from "react";
import ProgressBar from "@/components/ui/ProgressBar";
import { ACCEPTED_EXTENSIONS, precheckFile } from "@/hooks/useDocuments";
import { getErrorMessage } from "@/lib/api";
import { formatBytes } from "@/lib/format";

let nextId = 0;

export default function Dropzone({ onUpload }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);
  const [items, setItems] = useState([]);

  const update = (id, patch) => setItems((prev) => prev.map((it) => (it.id === id ? { ...it, ...patch } : it)));

  const handleFiles = async (fileList) => {
    const files = Array.from(fileList || []);
    if (!files.length) return;
    const queued = files.map((file) => {
      const problem = precheckFile(file);
      return { id: ++nextId, file, progress: 0, state: problem ? "error" : "queued", error: problem };
    });
    setItems((prev) => [...queued, ...prev]);

    for (const item of queued) {
      if (item.state === "error") continue;
      update(item.id, { state: "uploading" });
      try {
        await onUpload(item.file, (progress) => update(item.id, { progress }));
        setItems((prev) => prev.filter((it) => it.id !== item.id));
      } catch (err) {
        update(item.id, { state: "error", error: getErrorMessage(err, "Upload failed.") });
      }
    }
  };

  return (
    <div className="space-y-3">
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          handleFiles(e.dataTransfer.files);
        }}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-3xl border bg-card px-6 py-16 text-center transition-shadow focus-visible:outline-2 focus-visible:outline-ink ${
          dragging ? "border-ink shadow-soft" : "border-hairline hover:shadow-soft"
        }`}
      >
        <svg className="size-8 text-muted-soft" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V3m0 0L7.5 7.5M12 3l4.5 4.5M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5" />
        </svg>
        <p className="mt-4 text-[15px] font-medium text-ink">
          Drop files here or <span className="underline decoration-hairline-strong underline-offset-4">browse</span>
        </p>
        <p className="mt-1 text-sm text-muted">PDF, DOCX, TXT, or Markdown · up to 10 MB each</p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPTED_EXTENSIONS.join(",")}
          className="hidden"
          onChange={(e) => {
            handleFiles(e.target.files);
            e.target.value = "";
          }}
        />
      </div>

      {items.length > 0 && (
        <ul className="space-y-2">
          {items.map((item) => (
            <li key={item.id} className="rounded-2xl border border-hairline bg-card px-4 py-3">
              <div className="flex items-center justify-between gap-3 text-sm">
                <span className="truncate font-medium text-ink">{item.file.name}</span>
                <span className="shrink-0 text-xs text-muted">
                  {item.state === "error" ? (
                    <button
                      className="text-muted hover:text-ink"
                      onClick={() => setItems((prev) => prev.filter((it) => it.id !== item.id))}
                    >
                      Dismiss
                    </button>
                  ) : (
                    `${formatBytes(item.file.size)} · ${item.state === "queued" ? "Waiting" : `${item.progress}%`}`
                  )}
                </span>
              </div>
              {item.state === "error" ? (
                <p className="mt-1 text-sm text-error">{item.error}</p>
              ) : (
                <ProgressBar value={item.progress} className="mt-2" />
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
