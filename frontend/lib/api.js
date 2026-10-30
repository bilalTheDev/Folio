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

  return fetch(url, {
    ...options,
    credentials: "include",
    headers: {
      ...(options.headers || {}),
    },
  });
}
