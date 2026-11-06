import axios from "axios";
import { useAuthStore } from "./authStore";

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  timeout: 120000,
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token && !config.headers.Authorization) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshPromise = null;

// Concurrent 401s share one refresh call so the rotated cookie is not raced.
export function refreshSession() {
  if (!refreshPromise) {
    refreshPromise = axios
      .post(`${API_URL}/auth/refresh`, null, { withCredentials: true })
      .then((res) => {
        useAuthStore.getState().setSession(res.data);
        return res.data;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const isAuthCall = original?.url?.startsWith("/auth/");
    if (error.response?.status === 401 && original && !original._retried && !isAuthCall) {
      original._retried = true;
      try {
        const session = await refreshSession();
        original.headers.Authorization = `Bearer ${session.access_token}`;
        return api(original);
      } catch {
        useAuthStore.getState().clear();
        if (typeof window !== "undefined" && !window.location.pathname.startsWith("/signin")) {
          window.location.assign(`/signin?next=${encodeURIComponent(window.location.pathname)}`);
        }
      }
    }
    return Promise.reject(error);
  }
);

export function getErrorMessage(error, fallback = "Something went wrong. Please try again.") {
  if (!error) return fallback;
  if (error.code === "ECONNABORTED") return "The request timed out. Please try again.";
  if (!error.response) return "Can't reach the Folio server. Check your connection and try again.";
  const detail = error.response.data?.detail;
  if (typeof detail === "string" && detail) return detail;
  if (error.response.status === 402) {
    return "Your Hugging Face token has no Inference Provider credits. Add credits, upgrade to PRO, or switch to a native provider key in Settings.";
  }
  if (error.response.status === 413) return "That file is larger than 10 MB.";
  if (error.response.status === 429) return "Too many requests. Wait a moment and try again.";
  return fallback;
}

export function getErrorCode(error) {
  return error?.response?.data?.code || null;
}
