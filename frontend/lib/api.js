/**
 * Fetch helper for Folio API routes under /api.
 *
 * @param {string} path - Path relative to /api (e.g. "/health" or "health")
 * @param {RequestInit} [options]
 * @returns {Promise<Response>}
 */
export function apiFetch(path, options = {}) {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  const url = normalized.startsWith("/api") ? normalized : `/api${normalized}`;

  const headers = new Headers(options.headers || {});
  if (typeof window !== "undefined") {
    const key = window.sessionStorage.getItem("folio_provider_key");
    if (key && !headers.has("X-Provider-Key")) {
      headers.set("X-Provider-Key", key);
    }
    const token = window.sessionStorage.getItem("folio_session_token");
    if (token && !headers.has("Authorization")) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  return fetch(url, {
    ...options,
    credentials: "include",
    headers,
  });
}

export function saveProviderKey(key) {
  if (typeof window === "undefined") return;
  if (key) window.sessionStorage.setItem("folio_provider_key", key);
  else window.sessionStorage.removeItem("folio_provider_key");
}

export function getProviderKey() {
  if (typeof window === "undefined") return "";
  return window.sessionStorage.getItem("folio_provider_key") || "";
}
