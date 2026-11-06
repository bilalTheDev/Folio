export function sourceLabel(source) {
  const name = source.filename || "Deleted document";
  return source.page_or_section ? `${name} · ${source.page_or_section}` : name;
}

export default function CitationChip({ index, source, active, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-expanded={active}
      className={`inline-flex max-w-full items-center gap-1.5 rounded-full px-2.5 py-1 text-xs ring-1 ring-inset transition-colors ${
        active ? "bg-strong text-ink ring-ink" : "bg-card text-body ring-hairline hover:shadow-soft"
      }`}
    >
      <span className={`font-medium ${active ? "text-ink" : "text-muted-soft"}`}>{index + 1}</span>
      <span className="truncate">{sourceLabel(source)}</span>
    </button>
  );
}
