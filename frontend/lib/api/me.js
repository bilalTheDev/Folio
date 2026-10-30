import { apiFetch, readApiError } from "@/lib/api/client";

export async function getMe() {
  const res = await apiFetch("/me");
  if (!res.ok) throw new Error(await readApiError(res));
  return res.json();
}

export async function updateMe(body) {
  const res = await apiFetch("/me", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await readApiError(res));
  return res.json();
}

export async function rememberKey(provider, key) {
  const res = await apiFetch("/me/keys", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider, key }),
  });
  if (!res.ok && res.status !== 204) throw new Error(await readApiError(res));
}

export async function forgetKey(provider) {
  const res = await apiFetch(`/me/keys/${provider}`, { method: "DELETE" });
  if (!res.ok && res.status !== 204) throw new Error(await readApiError(res));
}
