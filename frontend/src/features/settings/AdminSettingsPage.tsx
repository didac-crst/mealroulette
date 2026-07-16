import type { ReactNode } from "react";
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

import { PageShell, PageLoadingState, SettingsTile } from "../../components/ui";
import { useAuth } from "../auth/AuthContext";
import { HouseholdClock } from "./HouseholdClock";
import {
  SettingsBackupIcon,
  SettingsHouseholdIcon,
  SettingsIngredientsIcon,
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

const HOUSEHOLD_TILES: SettingsTileConfig[] = [
  {
    to: "/settings/members",
    title: "Household",
    description: "Name, invite links, members, and roles.",
    icon: <SettingsHouseholdIcon />,
  },
];

const INTEGRATION_TILES: SettingsTileConfig[] = [
  {
    to: "/settings/telegram",
    title: "Telegram",
    description: "Daily reminders, bot commands, subscribers.",
    icon: <SettingsTelegramIcon />,
  },
  {
    to: "/settings/backups",
    title: "Backups",
    description: "JSON export, schedule, retention, and manual runs.",
    icon: <SettingsBackupIcon />,
  },
];

const CATALOG_TILES: SettingsTileConfig[] = [
  {
    to: "/ingredients",
    title: "Ingredients",
    description: "Catalog, aliases, units, and conversions.",
    icon: <SettingsIngredientsIcon />,
  },
];

function SettingsGroup({ heading, tiles }: { heading: string; tiles: SettingsTileConfig[] }) {
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
  const { isPlatformAdmin, isHouseholdAdmin, loading } = useAuth();
  const navigate = useNavigate();
  const canAccessSettings = isPlatformAdmin || isHouseholdAdmin;

  useEffect(() => {
    if (!loading && !canAccessSettings) {
      navigate("/today");
    }
  }, [canAccessSettings, loading, navigate]);

  if (loading) {
    return (
      <div className="admin-page">
        <PageLoadingState message="Loading settings…" />
      </div>
    );
  }

  if (!canAccessSettings) {
    return null;
  }

  return (
    <div className="admin-page">
      <PageShell
        title="Settings"
        subtitle={
          isHouseholdAdmin
            ? "Household admin — members, meal rules, and automation."
            : "Platform admin — installation catalog and integrations."
        }
      >
        <HouseholdClock />
        {isHouseholdAdmin ? <SettingsGroup heading="Household" tiles={HOUSEHOLD_TILES} /> : null}
        {isHouseholdAdmin ? <SettingsGroup heading="Meal planning" tiles={PLANNING_TILES} /> : null}
        {isPlatformAdmin ? <SettingsGroup heading="Integrations" tiles={INTEGRATION_TILES} /> : null}
        {isPlatformAdmin ? <SettingsGroup heading="Catalog" tiles={CATALOG_TILES} /> : null}
      </PageShell>
    </div>
  );
}
