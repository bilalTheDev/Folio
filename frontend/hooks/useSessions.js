"use client";

import { useEffect } from "react";
import { create } from "zustand";
import { api, getErrorMessage } from "@/lib/api";
import { useAuthStore } from "@/lib/authStore";

const byUpdated = (a, b) => new Date(b.updated_at) - new Date(a.updated_at);

// Shared by the sidebar, history page, and chat view so a sent message re-sorts and retitles everywhere.
export const useSessionsStore = create((set, get) => ({
  sessions: [],
  // idle | loading | ready | error
  status: "idle",
  error: "",

  load: async () => {
    if (get().status === "idle" || get().status === "error") set({ status: "loading" });
    try {
      const { data } = await api.get("/chat/sessions", { params: { limit: 200 } });
      set({ sessions: data, status: "ready", error: "" });
    } catch (err) {
      set({ status: "error", error: getErrorMessage(err, "Couldn't load your chats.") });
    }
  },

  upsert: (session) =>
    set((state) => {
      const existing = state.sessions.find((s) => s.id === session.id);
      const merged = { ...existing, ...session, last_message: session.last_message ?? existing?.last_message };
      return { sessions: [merged, ...state.sessions.filter((s) => s.id !== session.id)].sort(byUpdated) };
    }),

  create: async (title) => {
    const { data } = await api.post("/chat/sessions", title ? { title } : {});
    get().upsert(data);
    return data;
  },

  rename: async (id, title) => {
    const { data } = await api.patch(`/chat/sessions/${id}`, { title });
    set((state) => ({ sessions: state.sessions.map((s) => (s.id === id ? { ...s, ...data } : s)) }));
    return data;
  },

  remove: async (id) => {
    await api.delete(`/chat/sessions/${id}`);
    set((state) => ({ sessions: state.sessions.filter((s) => s.id !== id) }));
  },
}));

export function useSessions() {
  const store = useSessionsStore();
  const { status, load } = store;
  const authStatus = useAuthStore((s) => s.status);

  useEffect(() => {
    if (authStatus !== "authenticated") return;
    if (status === "idle") load();
  }, [authStatus, status, load]);

  return store;
}

export function filterSessions(sessions, query) {
  const q = query.trim().toLowerCase();
  if (!q) return sessions;
  return sessions.filter((s) => s.title.toLowerCase().includes(q));
}
