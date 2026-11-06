"use client";

import { useCallback, useEffect, useState } from "react";
import { api, getErrorMessage } from "@/lib/api";
import { useAuthStore } from "@/lib/authStore";

export function useProviders() {
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const authStatus = useAuthStore((s) => s.status);

  const load = useCallback(
    () =>
      api
        .get("/providers")
        .then(({ data }) => {
          setProviders(data);
          setError("");
        })
        .catch((err) => setError(getErrorMessage(err, "Couldn't load the list of providers.")))
        .finally(() => setLoading(false)),
    []
  );

  useEffect(() => {
    if (authStatus !== "authenticated") return;
    load();
  }, [authStatus, load]);

  const refresh = useCallback(() => {
    setLoading(true);
    return load();
  }, [load]);

  return { providers, loading, error, refresh };
}
