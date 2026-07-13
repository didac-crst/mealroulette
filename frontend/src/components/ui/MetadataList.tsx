import type { ReactNode } from "react";

export type MetadataItem = {
  label: ReactNode;
  value: ReactNode;
};

export type MetadataListProps = {
  items: MetadataItem[];
  className?: string;
};

export function MetadataList({ items, className }: MetadataListProps) {
  return (
    <dl className={["metadata-list", className].filter(Boolean).join(" ")}>
      {items.map((item, index) => (
        <div key={index} className="metadata-list-row">
          <dt className="metadata-list-label">{item.label}</dt>
          <dd className="metadata-list-value">{item.value}</dd>
        </div>
      ))}
    </dl>
  );
}
