import type { ReactNode } from "react";

import { PageShell, PageLoadingState, SettingsTile } from "../../components/ui";
import { useAuth } from "../auth/AuthContext";
import { HouseholdClock } from "./HouseholdClock";
import {
  SettingsBackupIcon,
  SettingsHouseholdIcon,
  SettingsIngredientsIcon,
  SettingsPasswordIcon,
  SettingsSchedulerIcon,
  SettingsTargetsIcon,
  SettingsTelegramIcon,
} from "./settingsIcons";

type SettingsTileConfig = {
  to: string;
  title: string;
  description: string;
  icon: ReactNode;
};

const ACCOUNT_TILES: SettingsTileConfig[] = [
  {
    to: "/settings/password",
    title: "Password",
    description: "Change your account password.",
    icon: <SettingsPasswordIcon />,
  },
  {
    to: "/settings/telegram",
    title: "Telegram",
    description: "Link your account, notification preferences, and daily reminders.",
    icon: <SettingsTelegramIcon />,
  },
];

const PLANNING_TILES: SettingsTileConfig[] = [
  {
    to: "/settings/targets",
    title: "Weekly targets",
    description: "How many fish, meat, pasta, and rice meals per week.",
    icon: <SettingsTargetsIcon />,
  },
  {
    to: "/settings/scheduler",
    title: "Auto roulette",
    description: "When to generate next week and Telegram “New roulette”.",
    icon: <SettingsSchedulerIcon />,
  },
];

const BACKUP_TILE: SettingsTileConfig = {
  to: "/settings/backups",
  title: "Backups",
  description: "JSON export, schedule, retention, and manual runs.",
  icon: <SettingsBackupIcon />,
};

const CATALOG_TILES: SettingsTileConfig[] = [
  {
    to: "/ingredients",
    title: "Ingredients",
    description: "Catalog, aliases, units, and conversions.",
    icon: <SettingsIngredientsIcon />,
  },
];

function SettingsGroup({ heading, tiles }: { heading: string; tiles: SettingsTileConfig[] }) {
  if (tiles.length === 0) {
    return null;
  }
  return (
    <div className="settings-group">
      <h2 className="settings-group-title">{heading}</h2>
      <ul className="settings-tile-list">
        {tiles.map((tile) => (
          <li key={tile.to}>
            <SettingsTile to={tile.to} title={tile.title} description={tile.description} icon={tile.icon} />
          </li>
        ))}
      </ul>
    </div>
  );
}

export function AdminSettingsPage() {
  const { isHouseholdAdmin, isPlatformAdmin, hasHousehold, loading } = useAuth();

  if (loading) {
    return (
      <div className="admin-page">
        <PageLoadingState message="Loading settings…" />
      </div>
    );
  }

  const memberTiles: SettingsTileConfig[] = isHouseholdAdmin
    ? [
        {
          to: "/settings/members",
          title: "Household settings",
          description: "Rename the household, invite people, and manage roles.",
          icon: <SettingsHouseholdIcon />,
        },
      ]
    : [];

  const householdIntegrations: SettingsTileConfig[] = [...(isPlatformAdmin ? [BACKUP_TILE] : [])];

  return (
    <div className="admin-page">
      <PageShell title="Settings" subtitle="Your account and household preferences.">
        {hasHousehold ? <HouseholdClock /> : null}
        <SettingsGroup heading="Account" tiles={ACCOUNT_TILES} />
        {isHouseholdAdmin ? <SettingsGroup heading="Household" tiles={memberTiles} /> : null}
        {isHouseholdAdmin ? <SettingsGroup heading="Meal planning" tiles={PLANNING_TILES} /> : null}
        {householdIntegrations.length > 0 ? (
          <SettingsGroup heading="Integrations" tiles={householdIntegrations} />
        ) : null}
        {isPlatformAdmin ? <SettingsGroup heading="Catalog" tiles={CATALOG_TILES} /> : null}
      </PageShell>
    </div>
  );
}
