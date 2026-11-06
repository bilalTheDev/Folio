"use client";

import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import Input, { Field } from "@/components/ui/Input";
import { useAuth } from "@/hooks/useAuth";
import { api, getErrorMessage } from "@/lib/api";

export function TokenHelp({ mode }) {
  if (!mode) return null;
  return (
    <div className="rounded-2xl border border-hairline bg-card p-6 text-[15px] leading-relaxed text-body">
      <p className="caption-upper text-muted">How to get a key</p>
      <p className="mt-3 font-medium text-ink">Create a key from the provider, then paste it here.</p>
      <ol className="mt-2 list-decimal space-y-1 pl-5">
        <li>
          Open{" "}
          <a
            href={mode.docs_url}
            target="_blank"
            rel="noreferrer"
            className="font-medium text-ink underline decoration-hairline-strong underline-offset-4 hover:decoration-ink"
          >
            {mode.docs_url.replace(/^https?:\/\//, "").replace(/\/$/, "")}
          </a>{" "}
          and create a key.
        </li>
        <li>
          Paste it here. It starts with <span className="font-mono">{mode.token_prefix || "the provider prefix"}</span>.
        </li>
      </ol>
      <p className="mt-2 text-muted">Folio encrypts the key and never shows it again in full.</p>
    </div>
  );
}

export default function CredentialForm({
  provider,
  authMode,
  catalog,
  submitLabel = "Save key",
  onSaved,
  existingMasked,
}) {
  const { syncUser } = useAuth();
  const [visible, setVisible] = useState(false);
  const [serverError, setServerError] = useState("");
  const [saved, setSaved] = useState(false);
  const mode = useMemo(
    () => catalog?.auth_modes?.find((m) => m.id === authMode) || null,
    [catalog, authMode]
  );
  const models = mode?.models || [];
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({
    mode: "onTouched",
    defaultValues: { model: models[0]?.id || "", token: "" },
  });

  const prefix = mode?.token_prefix || "";

  const onSubmit = async ({ token, model }) => {
    setServerError("");
    setSaved(false);
    try {
      const { data } = await api.patch("/users/me/credentials", {
        provider,
        auth_mode: authMode,
        token: token.trim(),
        model,
      });
      const updated = await syncUser(data);
      reset({ token: "", model });
      setVisible(false);
      setSaved(true);
      await onSaved?.(updated);
    } catch (err) {
      setServerError(getErrorMessage(err, "Couldn't save your key. Please try again."));
    }
  };

  if (!mode) return <Alert>That provider mode isn't available.</Alert>;

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
      {existingMasked && (
        <p className="text-sm text-body">
          Saved key: <code className="rounded-md bg-strong px-1.5 py-0.5 text-ink">{existingMasked}</code>
        </p>
      )}
      <Alert>{serverError}</Alert>
      {saved && !onSaved && <Alert tone="success">Key saved. New answers will use this provider.</Alert>}

      <Field label="Model" htmlFor="credential-model" error={errors.model?.message}>
        <select
          id="credential-model"
          className="block h-11 w-full rounded-lg bg-card px-3 text-sm text-ink ring-1 ring-inset ring-hairline-strong focus:outline-none focus:ring-2 focus:ring-ink"
          {...register("model", { required: "Pick a model." })}
        >
          {models.map((model) => (
            <option key={model.id} value={model.id}>
              {model.label || model.id}
            </option>
          ))}
        </select>
      </Field>

      <Field label={existingMasked ? "Replace key" : "API key"} htmlFor="credential-token" error={errors.token?.message}>
        <div className="relative">
          <Input
            id="credential-token"
            type={visible ? "text" : "password"}
            autoComplete="off"
            spellCheck={false}
            placeholder={`${prefix || ""}…`}
            className="pr-16 font-mono"
            invalid={!!errors.token}
            {...register("token", {
              required: "Paste your API key.",
              validate: (v) => {
                const value = v.trim();
                if (/\s/.test(value)) return "API keys cannot contain spaces.";
                if (prefix && !value.startsWith(prefix)) return `This key should start with ${prefix}.`;
                return true;
              },
            })}
          />
          <button
            type="button"
            onClick={() => setVisible((v) => !v)}
            className="absolute inset-y-0 right-0 px-3 text-xs font-medium text-muted hover:text-ink"
            aria-label={visible ? "Hide key" : "Show key"}
          >
            {visible ? "Hide" : "Show"}
          </button>
        </div>
      </Field>

      <Button type="submit" loading={isSubmitting}>
        {submitLabel}
      </Button>
    </form>
  );
}
