import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import {
  Breadcrumb,
  Button,
  ChoiceCard,
  DisclosureSection,
  FormSaveStatus,
  PageHeader,
  PageShell,
  SegmentedControl,
  SettingsTile,
  StatusBadge,
} from "./index";
import { LONG_LABEL_FIXTURES } from "../../lib/longLabelFixtures";

const de = LONG_LABEL_FIXTURES.de;

describe("long label layout smoke (German)", () => {
  it("renders PageHeader with long title and subtitle", () => {
    render(<PageHeader title={de.pageTitle} subtitle={de.subtitle} />);

    expect(screen.getByRole("heading", { level: 1, name: de.pageTitle })).toBeInTheDocument();
    expect(screen.getByText(de.subtitle)).toHaveClass("page-header-subtitle");
  });

  it("renders PageShell with long title, subtitle, and breadcrumbs on a settings route", () => {
    render(
      <MemoryRouter initialEntries={["/settings/scheduler"]}>
        <PageShell title={de.pageTitle} subtitle={de.subtitle} />
      </MemoryRouter>,
    );

    expect(screen.getByRole("navigation", { name: "Breadcrumb" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1, name: de.pageTitle })).toBeInTheDocument();
    expect(screen.getByText(de.subtitle)).toHaveClass("page-header-subtitle");
  });

  it("renders Breadcrumb with long German segments", () => {
    render(
      <MemoryRouter>
        <Breadcrumb
          items={[
            { label: de.breadcrumbSegment, to: "/settings" },
            { label: de.breadcrumbCurrent },
          ]}
        />
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: de.breadcrumbSegment })).toHaveClass("breadcrumb-link");
    expect(screen.getByText(de.breadcrumbCurrent)).toHaveClass("breadcrumb-current");
  });

  it("renders Button with long accessible name", () => {
    render(<Button>{de.button}</Button>);

    expect(screen.getByRole("button", { name: de.button })).toBeInTheDocument();
  });

  it("renders StatusBadge with long canonical status text", () => {
    render(<StatusBadge variant="success">{de.status}</StatusBadge>);

    expect(screen.getByText(de.status)).toHaveClass("status-badge");
  });

  it("renders settings tile text without losing content", () => {
    render(
      <MemoryRouter>
        <SettingsTile
          to="/settings/scheduler"
          title={de.settingsLinkTitle}
          description={de.settingsLinkDescription}
          icon={<span aria-hidden>⚙</span>}
        />
      </MemoryRouter>,
    );

    expect(screen.getByText(de.settingsLinkTitle)).toHaveClass("settings-tile-title");
    expect(screen.getByText(de.settingsLinkDescription)).toHaveClass("settings-tile-description");
  });

  it("renders ChoiceCard with long title and description", () => {
    render(<ChoiceCard title={de.choiceCardTitle} description={de.choiceCardDescription} />);

    expect(screen.getByText(de.choiceCardTitle)).toHaveClass("choice-card-title");
    expect(screen.getByText(de.choiceCardDescription)).toHaveClass("choice-card-description");
  });

  it("renders SegmentedControl with long option labels", () => {
    render(
      <SegmentedControl
        ariaLabel="Review filter"
        value="needs_review"
        onChange={() => undefined}
        options={[
          { value: "all", label: "Alle Mahlzeiten" },
          { value: "needs_review", label: de.segmentLabel },
        ]}
      />,
    );

    expect(screen.getByRole("button", { name: de.segmentLabel })).toHaveAttribute("aria-pressed", "true");
  });

  it("renders DisclosureSection summary with long title", () => {
    render(
      <DisclosureSection title={de.disclosureTitle}>
        <p>Hidden content</p>
      </DisclosureSection>,
    );

    expect(screen.getByText(de.disclosureTitle)).toHaveClass("disclosure-section-summary");
  });

  it("renders FormSaveStatus for unsaved German workflow copy", () => {
    render(<FormSaveStatus status="unsaved" />);

    expect(screen.getByRole("status")).toHaveTextContent("Unsaved changes");
  });
});
