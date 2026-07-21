import { ReactNode } from "react";

export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon: ReactNode;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="mx-auto flex max-w-md animate-fade-in flex-col items-center py-24 text-center">
      <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl border border-border bg-surface text-accent">
        {icon}
      </div>
      <h2 className="mb-2 font-serif text-2xl font-semibold text-ink">{title}</h2>
      <p className="mb-6 text-muted">{description}</p>
      {action}
    </div>
  );
}
