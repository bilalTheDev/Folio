function sourceWhere(source) {
  const heading = source.section_heading;
  const page = source.page_number;
  if (page && heading) return `Page ${page} · ${heading}`;
  if (heading) return heading;
  if (page) return `Page ${page}`;
  return source.page_or_section || "";
}

export default function SourcePanel({ index, source, onClose }) {
  const where = sourceWhere(source);
  return (
    <div className="mt-3 rounded-2xl border border-hairline bg-card p-5" role="region" aria-label={`Source ${index + 1}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="caption-upper text-muted">Source {index + 1}</p>
          <p className="mt-1 truncate text-sm font-medium text-ink">
            {source.filename || "Deleted document"}
          </p>
          {where && <p className="text-xs text-muted">{where}</p>}
        </div>
        <button
          type="button"
          onClick={onClose}
          className="shrink-0 rounded-full px-2 py-1 text-xs text-muted hover:bg-card hover:text-ink"
        >
          Close
        </button>
      </div>
      <blockquote className="mt-3 max-h-72 overflow-y-auto whitespace-pre-wrap border-l-2 border-hairline-strong pl-3 text-sm leading-relaxed text-body">
        {source.chunk_text}
      </blockquote>
    </div>
  );
}
