"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import ProviderCard from "@/components/onboarding/ProviderCard";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import { PageLoader } from "@/components/ui/Spinner";
import { useAuth } from "@/hooks/useAuth";
import { useProviders } from "@/hooks/useProviders";
import { tokenRoute } from "@/lib/routes";

export default function ProviderStep() {
  const router = useRouter();
  const { user } = useAuth();
  const { providers, loading, error, refresh } = useProviders();
  const [selection, setSelection] = useState({
    provider: user?.selected_provider || null,
    auth_mode: user?.auth_mode || null,
  });

  const continueToToken = () => {
    if (!selection.provider || !selection.auth_mode) return;
    router.push(tokenRoute(selection.provider, selection.auth_mode));
  };

  return (
    <div>
      <p className="caption-upper text-muted">Step 2 of 3</p>
      <h1 className="display-md mt-3 text-ink">Choose a provider</h1>
      <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-body">
        Use a native Groq or Cerebras key (often free-tier) or route through Hugging Face Inference Providers.
        You can add more providers later in Settings.
      </p>

      <div className="mt-8">
        {loading ? (
          <PageLoader label="Loading providers…" />
        ) : error ? (
          <Alert
            action={
              <button onClick={refresh} className="shrink-0 font-medium underline">
                Retry
              </button>
            }
          >
            {error}
          </Alert>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {providers.map((provider) => (
              <ProviderCard key={provider.id} provider={provider} selection={selection} onSelect={setSelection} />
            ))}
          </div>
        )}
      </div>

      <div className="mt-10 flex items-center justify-between border-t border-hairline pt-6">
        <Button variant="ghost" href="/onboarding/upload">
          Back
        </Button>
        <Button onClick={continueToToken} disabled={!selection.provider || !selection.auth_mode}>
          Continue
        </Button>
      </div>
    </div>
  );
}
