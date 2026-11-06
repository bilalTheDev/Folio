"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, getErrorMessage } from "@/lib/api";
import { useAuthStore } from "@/lib/authStore";

export const MAX_UPLOAD_BYTES = Number(process.env.NEXT_PUBLIC_MAX_UPLOAD_BYTES) || 10 * 1024 * 1024;
export const ACCEPTED_EXTENSIONS = [".pdf", ".docx", ".txt", ".md"];

const POLL_MS = 2500;
const isBusy = (doc) => doc.status === "uploaded" || doc.status === "indexing";

export function precheckFile(file) {
  const ext = `.${file.name.split(".").pop()}`.toLowerCase();
  if (!ACCEPTED_EXTENSIONS.includes(ext)) return "Only PDF, DOCX, TXT, and Markdown files are supported.";
  if (file.size === 0) return "This file is empty.";
  if (file.size > MAX_UPLOAD_BYTES) return "This file is larger than 10 MB.";
  return null;
}

export function useDocuments({ poll = true } = {}) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const timer = useRef(null);
  const authStatus = useAuthStore((s) => s.status);

  const refresh = useCallback(
    () =>
      api
        .get("/documents")
        .then(({ data }) => {
          setDocuments(data);
          setError("");
          return data;
        })
        .catch((err) => {
          setError(getErrorMessage(err, "Couldn't load your documents."));
          return null;
        })
        .finally(() => setLoading(false)),
    []
  );

  useEffect(() => {
    if (authStatus !== "authenticated") return;
    refresh();
  }, [authStatus, refresh]);

  // Poll while anything is still being processed so status badges update on their own.
  const anyBusy = documents.some(isBusy);
  useEffect(() => {
    if (authStatus !== "authenticated" || !poll || !anyBusy) return undefined;
    timer.current = setInterval(refresh, POLL_MS);
    return () => clearInterval(timer.current);
  }, [authStatus, poll, anyBusy, refresh]);

  const upload = useCallback(async (file, onProgress) => {
    const form = new FormData();
    form.append("file", file);
    const { data } = await api.post("/documents/upload", form, {
      onUploadProgress: (e) => {
        if (e.total) onProgress?.(Math.round((e.loaded / e.total) * 100));
      },
    });
    setDocuments((prev) => [data, ...prev.filter((d) => d.id !== data.id)]);
    return data;
  }, []);

  const remove = useCallback(async (id) => {
    await api.delete(`/documents/${id}`);
    setDocuments((prev) => prev.filter((d) => d.id !== id));
  }, []);

  const reindex = useCallback(async (id) => {
    const { data } = await api.post(`/documents/${id}/reindex`);
    setDocuments((prev) => prev.map((d) => (d.id === id ? data : d)));
    return data;
  }, []);

  return { documents, loading, error, refresh, upload, remove, reindex };
}
