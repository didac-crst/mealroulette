import type { ReactNode } from "react";

export type SettingsSectionHeaderProps = {
  title: ReactNode;
  description?: ReactNode;
  trailing?: ReactNode;
  className?: string;
};

export function SettingsSectionHeader({ title, description, trailing, className }: SettingsSectionHeaderProps) {
  return (
    <header className={["settings-section-header", className].filter(Boolean).join(" ")}>
      <div className="settings-section-header-text">
        <h2 className="settings-section-header-title">{title}</h2>
        {description ? <p className="settings-section-header-description muted">{description}</p> : null}
      </div>
      {trailing ? <div className="settings-section-header-trailing">{trailing}</div> : null}
    </header>
  );
}

