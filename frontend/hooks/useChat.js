"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useSessionsStore } from "@/hooks/useSessions";
import { api, getErrorCode, getErrorMessage } from "@/lib/api";
import { useAuthStore } from "@/lib/authStore";

// The first message of a new chat is typed on /app/chat, then sent once /app/chat/[id] mounts.
const pendingFirstMessages = new Map();

export function queueFirstMessage(sessionId, content) {
  pendingFirstMessages.set(sessionId, content);
}

let tempId = 0;

export function useChat(sessionId) {
  const [messages, setMessages] = useState([]);
  // loading | ready | error | missing
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState("");
  const [sending, setSending] = useState(false);
  const upsertSession = useSessionsStore((s) => s.upsert);
  const authStatus = useAuthStore((s) => s.status);
  const loadSeq = useRef(0);

  const send = useCallback(
    async (content) => {
      const local = {
        id: `local-${++tempId}`,
        session_id: sessionId,
        role: "user",
        content,
        sources: [],
        created_at: new Date().toISOString(),
        pending: true,
      };
      setMessages((prev) => [...prev.filter((m) => !m.failed), local]);
      setSending(true);
      try {
        const { data } = await api.post(`/chat/sessions/${sessionId}/messages`, { content });
        const { user_message, assistant_message } = data;
        const replaced = new Set([local.id, user_message.id, assistant_message.id]);
        setMessages((prev) => [...prev.filter((m) => !replaced.has(m.id)), user_message, assistant_message]);
        upsertSession(data.session);
        return true;
      } catch (err) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === local.id
              ? {
                  ...m,
                  pending: false,
                  failed: true,
                  error: getErrorMessage(err, "Couldn't get an answer. Please try again."),
                  errorCode: getErrorCode(err),
                }
              : m
          )
        );
        return false;
      } finally {
        setSending(false);
      }
    },
    [sessionId, upsertSession]
  );

  const load = useCallback(async () => {
    const seq = ++loadSeq.current;
    try {
      const { data } = await api.get(`/chat/sessions/${sessionId}/messages`);
      if (seq !== loadSeq.current) return;
      // Keep messages that are still in flight or failed locally; the server doesn't know about them yet.
      setMessages((prev) => {
        const serverIds = new Set(data.map((m) => m.id));
        const local = prev.filter((m) => m.session_id === sessionId && (m.pending || m.failed) && !serverIds.has(m.id));
        return [...data, ...local];
      });
      setStatus("ready");
      setError("");
    } catch (err) {
      if (seq !== loadSeq.current) return;
      if (err.response?.status === 404) setStatus("missing");
      else {
        setStatus("error");
        setError(getErrorMessage(err, "Couldn't load this chat."));
      }
    }
  }, [sessionId]);

  useEffect(() => {
    if (authStatus !== "authenticated") return;
    load().then(() => {
      const first = pendingFirstMessages.get(sessionId);
      if (first) {
        pendingFirstMessages.delete(sessionId);
        send(first);
      }
    });
  }, [authStatus, sessionId, load, send]);

  const retry = useCallback(
    (message) => {
      setMessages((prev) => prev.filter((m) => m.id !== message.id));
      return send(message.content);
    },
    [send]
  );

  return { messages, status, error, sending, send, retry, reload: load };
}
