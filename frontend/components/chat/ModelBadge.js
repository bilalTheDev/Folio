"use client";

import { useAuthStore } from "@/lib/authStore";

const PROVIDER_NAMES = { groq: "Groq", cerebras: "Cerebras", huggingface: "Hugging Face", auto: "Hugging Face" };

export function describeModel(provider, model, authMode) {
  if (!provider || !model) return null;
  const name = PROVIDER_NAMES[provider] || provider;
  const short = model.split("/").pop();
  const via = authMode === "hf_inference_providers" && provider !== "huggingface" ? `${name} via HF` : name;
  return { provider: via, model: short };
}

export default function ModelBadge({ className = "" }) {
  const user = useAuthStore((s) => s.user);
  const info = describeModel(user?.selected_provider, user?.selected_model, user?.auth_mode);
  if (!info) return null;
  return (
    <span
      title={`Answering via ${info.provider} — ${user.selected_model}`}
      className={`inline-flex items-center gap-1.5 rounded-full bg-strong px-2.5 py-1 text-xs font-medium text-ink ${className}`}
    >
      <span className="size-1.5 rounded-full bg-success" aria-hidden="true" />
      Answering via {info.provider} — {info.model}
    </span>
  );
}
