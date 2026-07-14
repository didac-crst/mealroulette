import type { ReactNode } from "react";
import { Link } from "react-router-dom";

export type SettingsTileProps = {
  to: string;
  title: ReactNode;
  description: ReactNode;
  icon: ReactNode;
};

export function SettingsTile({ to, title, description, icon }: SettingsTileProps) {
  return (
    <Link to={to} className="settings-tile">
      <span className="settings-tile-icon" aria-hidden>
        {icon}
      </span>
      <span className="settings-tile-body">
        <span className="settings-tile-title">{title}</span>
        <span className="settings-tile-description muted">{description}</span>
      </span>
    </Link>
  );
}
