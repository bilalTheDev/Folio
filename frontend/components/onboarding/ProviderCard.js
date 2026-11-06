export default function ProviderCard({ provider, selection, onSelect }) {
  const active = selection.provider === provider.id;

  return (
    <fieldset
      className={`rounded-2xl border p-6 transition-colors ${
        active ? "border-ink bg-card ring-1 ring-ink" : "border-hairline bg-card"
      }`}
    >
      <legend className="sr-only">{provider.name}</legend>
      <div>
        <p className="text-[18px] font-medium tracking-[0.01em] text-ink">{provider.name}</p>
        {provider.description && <p className="mt-1 text-[15px] leading-relaxed text-body">{provider.description}</p>}
      </div>
      <div className="mt-3 space-y-2">
        {provider.auth_modes.map((mode) => {
          const checked = active && selection.auth_mode === mode.id;
          return (
            <label
              key={mode.id}
              className={`flex cursor-pointer items-start gap-3 rounded-lg px-3 py-2 text-sm ring-1 ring-inset transition-colors ${
                checked ? "bg-card ring-ink" : "ring-hairline hover:bg-canvas-soft"
              }`}
            >
              <input
                type="radio"
                name="provider-mode"
                className="mt-0.5 size-4 accent-ink"
                checked={checked}
                onChange={() => onSelect({ provider: provider.id, auth_mode: mode.id })}
              />
              <span className="min-w-0">
                <span className="block font-medium text-ink">{mode.label}</span>
                {mode.hint && <span className="block text-xs text-muted">{mode.hint}</span>}
              </span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}
