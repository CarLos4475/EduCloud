/** Placeholder shapes for waiting states; the text is for screen readers only. */
export function Skeleton({
  lines = 3,
  label,
}: {
  lines?: number;
  label?: string;
}) {
  return (
    <div className="skeleton-block" role={label ? "status" : undefined}>
      {label && <span className="visually-hidden">{label}</span>}
      {Array.from({ length: lines }, (_, i) => (
        <span
          key={i}
          className="skeleton-line"
          aria-hidden="true"
          style={{ width: `${92 - ((i * 17) % 40)}%` }}
        />
      ))}
    </div>
  );
}

export function PageSkeleton({ label }: { label: string }) {
  return (
    <div className="page-skeleton" role="status" aria-live="polite">
      <span className="visually-hidden">{label}</span>
      <span className="skeleton-line skeleton-title" aria-hidden="true" />
      <Skeleton lines={2} />
      <div className="skeleton-cards" aria-hidden="true">
        {[0, 1, 2].map((i) => (
          <div key={i} className="skeleton-card resource-card">
            <Skeleton lines={3} />
          </div>
        ))}
      </div>
    </div>
  );
}
