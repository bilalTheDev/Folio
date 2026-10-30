import { apiFetch, readApiError } from "@/lib/api/client";

export async function listDocuments() {
  const res = await apiFetch("/documents");
  if (!res.ok) throw new Error(await readApiError(res));
  return res.json();
}

export async function uploadDocument(file) {
  const form = new FormData();
  form.append("file", file);
  const res = await apiFetch("/documents", { method: "POST", body: form });
  if (!res.ok) throw new Error(await readApiError(res));
  return res.json();
}

export async function deleteDocument(documentId) {
  const res = await apiFetch(`/documents/${documentId}`, { method: "DELETE" });
  if (!res.ok && res.status !== 204) throw new Error(await readApiError(res));
}
