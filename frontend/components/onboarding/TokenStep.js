"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect } from "react";
import CredentialForm, { TokenHelp } from "@/components/settings/CredentialForm";
import Button from "@/components/ui/Button";
import { PageLoader } from "@/components/ui/Spinner";
import { useAuth } from "@/hooks/useAuth";
import { useProviders } from "@/hooks/useProviders";
import { api } from "@/lib/api";
import { APP_HOME } from "@/lib/routes";

export default function TokenStep() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const provider = searchParams.get("provider");
  const authMode = searchParams.get("auth_mode");
  const { user, syncUser } = useAuth();
  const { providers, loading } = useProviders();

  useEffect(() => {
    if (!provider || !authMode) router.replace("/onboarding/provider");
  }, [provider, authMode, router]);

  const catalog = providers.find((p) => p.id === provider);
  const mode = catalog?.auth_modes?.find((m) => m.id === authMode);

  useEffect(() => {
    if (loading) return;
    if (provider && (!catalog || !mode)) router.replace("/onboarding/provider");
  }, [loading, provider, catalog, mode, router]);

  if (!provider || !authMode) return <PageLoader label="Redirecting…" />;

  const finish = async (updated) => {
    const { data } = await api.patch("/users/me/onboarding");
    const userOut = await syncUser(data || updated);
    if (userOut.onboarding_completed) router.replace(APP_HOME);
  };

  return (
    <div>
      <p className="caption-upper text-muted">Step 3 of 3</p>
      <h1 className="display-md mt-3 text-ink">Connect your {catalog?.name || "provider"} key</h1>
      <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-body">
        {mode?.hint || "Folio calls the model with your own key, so you stay in control of cost and access."}
      </p>

      <div className="mt-8 grid gap-8 md:grid-cols-[1fr_18rem]">
        {loading || !catalog ? (
          <PageLoader label="Loading models…" />
        ) : (
          <CredentialForm
            key={`${provider}-${authMode}`}
            provider={provider}
            authMode={authMode}
            catalog={catalog}
            existingMasked={user?.selected_provider === provider ? user.token_masked : null}
            submitLabel="Save and start chatting"
            onSaved={finish}
          />
        )}
        <TokenHelp mode={mode} />
      </div>

      <div className="mt-10 flex items-center justify-between border-t border-hairline pt-6">
        <Button variant="ghost" href="/onboarding/provider">
          Back
        </Button>
      </div>
    </div>
  );
}
