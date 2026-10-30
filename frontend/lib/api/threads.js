import { apiFetch, readApiError } from "@/lib/api/client";

export async function listThreads({ documentId, q } = {}) {
  const params = new URLSearchParams();
  if (documentId) params.set("document_id", documentId);
  if (q) params.set("q", q);
  const suffix = params.toString() ? `?${params}` : "";
  const res = await apiFetch(`/threads${suffix}`);
  if (!res.ok) throw new Error(await readApiError(res));
  return res.json();
}

export async function exportThread(threadId) {
  const res = await apiFetch(`/threads/${threadId}/export`);
  if (!res.ok) throw new Error(await readApiError(res));
  return res.blob();
}
