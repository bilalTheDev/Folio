"use client";

import { useCallback, useEffect, useState } from "react";
import { api, getErrorMessage } from "@/lib/api";
import { useAuthStore } from "@/lib/authStore";

export function useCredentials() {
  const authStatus = useAuthStore((s) => s.status);
  const [credentials, setCredentials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(
    () =>
      api
        .get("/users/me/credentials")
        .then(({ data }) => {
          setCredentials(data);
          setError("");
          return data;
        })
        .catch((err) => {
          setError(getErrorMessage(err, "Couldn't load your providers."));
          return null;
        })
        .finally(() => setLoading(false)),
    []
  );

  useEffect(() => {
    if (authStatus !== "authenticated") return;
    load();
  }, [authStatus, load]);

  return { credentials, loading, error, reload: load, setCredentials };
}
