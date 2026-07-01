"use client";

export default function PageHeader({
  title, subtitle, actions,
}: {
  readonly title: string;
  readonly subtitle?: string;
  readonly actions?: React.ReactNode;
}) {
  return (
    <div className="page-header">
      <div>
        <h2>{title}</h2>
        {subtitle && <div className="sub">{subtitle}</div>}
      </div>
      {actions && <div className="actions">{actions}</div>}
    </div>
  );
}
