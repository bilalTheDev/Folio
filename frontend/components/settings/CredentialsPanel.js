"use client";

import { useMemo, useState } from "react";
import CredentialForm, { TokenHelp } from "@/components/settings/CredentialForm";
import ProviderCard from "@/components/onboarding/ProviderCard";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import { PageLoader } from "@/components/ui/Spinner";
import { useAuth } from "@/hooks/useAuth";
import { useCredentials } from "@/hooks/useCredentials";
import { useProviders } from "@/hooks/useProviders";
import { api, getErrorMessage } from "@/lib/api";

const NAMES = { groq: "Groq", cerebras: "Cerebras", huggingface: "Hugging Face" };

export default function CredentialsPanel() {
  const { syncUser } = useAuth();
  const { providers, loading: loadingCatalog } = useProviders();
  const { credentials, loading, error, reload } = useCredentials();
  const [adding, setAdding] = useState(false);
  const [selection, setSelection] = useState({ provider: null, auth_mode: null });
  const [actionError, setActionError] = useState("");

  const catalog = useMemo(
    () => providers.find((p) => p.id === selection.provider),
    [providers, selection.provider]
  );
  const mode = catalog?.auth_modes?.find((m) => m.id === selection.auth_mode);

  const run = async (fn) => {
    setActionError("");
    try {
      const { data } = await fn();
      await syncUser(data);
      await reload();
    } catch (err) {
      setActionError(getErrorMessage(err, "Couldn't update providers."));
    }
  };

  if (loading || loadingCatalog) return <PageLoader label="Loading providers…" />;
  if (error) {
    return (
      <Alert
        action={
          <button onClick={reload} className="shrink-0 font-medium underline">
            Retry
          </button>
        }
      >
        {error}
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      <Alert>{actionError}</Alert>
      <ul className="space-y-3">
        {credentials.map((cred) => (
          <li key={cred.provider} className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-hairline bg-card px-5 py-5">
            <div>
              <p className="text-sm font-medium text-ink">
                {NAMES[cred.provider] || cred.provider}
                {cred.is_active && <span className="ml-2 text-xs font-normal text-success">Active</span>}
              </p>
              <p className="text-xs text-muted">
                {cred.auth_mode === "native" ? "Native key" : "Hugging Face Inference Providers"} · {cred.model} ·{" "}
                <code>{cred.token_masked}</code>
              </p>
            </div>
            <div className="flex gap-2">
              {!cred.is_active && (
                <Button
                  variant="secondary"
                  onClick={() => run(() => api.patch("/users/me/credentials/active", { provider: cred.provider }))}
                >
                  Use for chat
                </Button>
              )}
              <Button
                variant="ghost"
                onClick={() => run(() => api.delete(`/users/me/credentials/${cred.provider}`))}
              >
                Remove
              </Button>
            </div>
          </li>
        ))}
      </ul>

      {adding ? (
        <div className="space-y-6 rounded-2xl border border-hairline bg-card p-6">
          <p className="text-[18px] font-medium tracking-[0.01em] text-ink">Add a provider</p>
          <div className="grid gap-4 sm:grid-cols-2">
            {providers.map((provider) => (
              <ProviderCard key={provider.id} provider={provider} selection={selection} onSelect={setSelection} />
            ))}
          </div>
          {selection.provider && selection.auth_mode && catalog && (
            <div className="grid gap-6 md:grid-cols-[1fr_16rem]">
              <CredentialForm
                key={`${selection.provider}-${selection.auth_mode}`}
                provider={selection.provider}
                authMode={selection.auth_mode}
                catalog={catalog}
                submitLabel="Save provider"
                onSaved={async (updated) => {
                  await syncUser(updated);
                  await reload();
                  setAdding(false);
                  setSelection({ provider: null, auth_mode: null });
                }}
              />
              <TokenHelp mode={mode} />
            </div>
          )}
          <Button variant="ghost" onClick={() => setAdding(false)}>
            Cancel
          </Button>
        </div>
      ) : (
        <Button variant="secondary" onClick={() => setAdding(true)}>
          Add a provider
        </Button>
      )}
    </div>
  );
}
