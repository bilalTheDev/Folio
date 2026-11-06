"use client";

import SignoutButton from "@/components/auth/SignoutButton";
import { describeModel } from "@/components/chat/ModelBadge";
import Page from "@/components/layout/Page";
import CredentialsPanel from "@/components/settings/CredentialsPanel";
import Card from "@/components/ui/Card";
import { ThemePicker } from "@/components/ui/ThemeToggle";
import { useAuth } from "@/hooks/useAuth";
import { formatDate } from "@/lib/format";

function Section({ title, description, children }) {
  return (
    <Card className="p-8">
      <h2 className="display-sm text-ink">{title}</h2>
      {description && <p className="mt-2 text-[15px] leading-relaxed text-body">{description}</p>}
      <div className="mt-6">{children}</div>
    </Card>
  );
}

export default function SettingsView() {
  const { user } = useAuth();
  const current = describeModel(user?.selected_provider, user?.selected_model, user?.auth_mode);

  return (
    <Page
      eyebrow="Account"
      title="Settings"
      description="Manage your account, provider keys, and model."
      width="max-w-3xl"
    >
      <div className="space-y-6">
        <Section title="Appearance" description="Light keeps the off-white canvas. Dark uses the same ink and type, inverted.">
          <ThemePicker />
        </Section>

        <Section title="Account">
          <dl className="grid gap-4 text-[15px] sm:grid-cols-2">
            <div>
              <dt className="caption-upper text-muted">Email</dt>
              <dd className="mt-1.5 text-ink">{user?.email}</dd>
            </div>
            <div>
              <dt className="caption-upper text-muted">Member since</dt>
              <dd className="mt-1.5 text-ink">{formatDate(user?.created_at)}</dd>
            </div>
          </dl>
          <div className="mt-6 border-t border-hairline pt-4">
            <SignoutButton className="-ml-2" />
          </div>
        </Section>

        <Section
          title="Providers"
          description={
            current
              ? `Currently answering via ${current.provider} — ${current.model}.`
              : "Add a native Groq or Cerebras key, or a Hugging Face Inference Providers token."
          }
        >
          <CredentialsPanel />
        </Section>
      </div>
    </Page>
  );
}
