"use client";

import { useCallback } from "react";
import { api, refreshSession } from "@/lib/api";
import { useAuthStore } from "@/lib/authStore";

let bootstrapPromise = null;

// Restores the session from the refresh cookie once per page load.
export function bootstrapSession() {
  const { status } = useAuthStore.getState();
  if (status === "authenticated" || status === "anonymous") return Promise.resolve();
  if (!bootstrapPromise) {
    useAuthStore.getState().setStatus("loading");
    bootstrapPromise = refreshSession()
      .catch(() => useAuthStore.getState().clear())
      .finally(() => {
        bootstrapPromise = null;
      });
  }
  return bootstrapPromise;
}

export function useAuth() {
  const user = useAuthStore((s) => s.user);
  const status = useAuthStore((s) => s.status);
  const setSession = useAuthStore((s) => s.setSession);
  const setUser = useAuthStore((s) => s.setUser);
  const clear = useAuthStore((s) => s.clear);

  const signin = useCallback(
    async (email, password) => {
      const { data } = await api.post("/auth/signin", { email, password });
      setSession(data);
      return data.user;
    },
    [setSession]
  );

  const signup = useCallback(
    async (email, password) => {
      await api.post("/auth/signup", { email, password });
      return signin(email, password);
    },
    [signin]
  );

  const signout = useCallback(async () => {
    try {
      await api.post("/auth/signout");
    } finally {
      clear();
    }
  }, [clear]);

  const reloadUser = useCallback(async () => {
    const { data } = await api.get("/users/me");
    setUser(data);
    return data;
  }, [setUser]);

  // Settings endpoints return the updated user; fall back to /users/me if a response omits it.
  const syncUser = useCallback(
    async (data) => {
      if (data?.id && data?.onboarding) {
        setUser(data);
        return data;
      }
      return reloadUser();
    },
    [setUser, reloadUser]
  );

  return { user, status, signin, signup, signout, reloadUser, setUser, syncUser };
}
