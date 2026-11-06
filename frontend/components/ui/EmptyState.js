export default function EmptyState({ title, description, action, icon }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-hairline bg-card px-8 py-16 text-center">
      {icon && <div className="mb-4 text-muted-soft">{icon}</div>}
      <h3 className="display-sm text-ink">{title}</h3>
      {description && <p className="mt-3 max-w-sm text-[15px] leading-relaxed text-body">{description}</p>}
      {action && <div className="mt-8">{action}</div>}
    </div>
  );
}
