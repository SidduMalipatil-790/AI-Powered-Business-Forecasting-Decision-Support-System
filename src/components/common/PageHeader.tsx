import { ReactNode } from "react";

interface Props {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}

export function PageHeader({ eyebrow, title, description, actions }: Props) {
  return (
    <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4 mb-6 md:mb-8 animate-slide-up">
      <div>
        {eyebrow && (
          <div className="text-xs font-semibold uppercase tracking-[0.2em] text-primary mb-2">{eyebrow}</div>
        )}
        <h1 className="font-display text-3xl md:text-4xl font-bold tracking-tight">
          {title}
        </h1>
        {description && (
          <p className="text-muted-foreground mt-2 max-w-2xl">{description}</p>
        )}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}
