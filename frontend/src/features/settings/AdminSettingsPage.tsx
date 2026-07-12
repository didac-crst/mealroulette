import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import { HouseholdClock } from "./HouseholdClock";

type SettingsLink = {
  to: string;
  title: string;
  description: string;
};

const PLANNING_LINKS: SettingsLink[] = [
  {
    to: "/settings/targets",
    title: "Weekly targets",
    description: "How many fish, meat, pasta, and rice meals per week.",
  },
  {
    to: "/settings/scheduler",
    title: "Auto roulette",
    description: "When to generate next week and Telegram “New roulette”.",
  },
];

const INTEGRATION_LINKS: SettingsLink[] = [
  {
    to: "/settings/telegram",
    title: "Telegram",
    description: "Daily reminders, bot commands, subscribers.",
  },
];

const CATALOG_LINKS: SettingsLink[] = [
  {
    to: "/ingredients",
    title: "Ingredients",
    description: "Catalog, aliases, units, and conversions.",
  },
];

function SettingsGroup({ heading, links }: { heading: string; links: SettingsLink[] }) {
  return (
    <div className="settings-group">
      <h3 className="settings-group-title">{heading}</h3>
      <ul className="settings-link-list">
        {links.map((link) => (
          <li key={link.to}>
            <Link to={link.to} className="settings-link-card">
              <span className="settings-link-title">{link.title}</span>
              <span className="settings-link-description">{link.description}</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function AdminSettingsPage() {
  const { isAdmin, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && !isAdmin) {
      navigate("/review");
    }
  }, [isAdmin, loading, navigate]);

  if (loading) {
    return (
      <section className="card stack settings-page">
        <p className="muted">Loading…</p>
      </section>
    );
  }

  if (!isAdmin) {
    return null;
  }

  return (
    <section className="card stack settings-page">
      <div>
        <h2>Settings</h2>
        <p className="muted settings-page-subtitle">Household admin — meal rules, automation, and catalog.</p>
      </div>

      <HouseholdClock />

      <SettingsGroup heading="Meal planning" links={PLANNING_LINKS} />
      <SettingsGroup heading="Integrations" links={INTEGRATION_LINKS} />
      <SettingsGroup heading="Catalog" links={CATALOG_LINKS} />
    </section>
  );
}
