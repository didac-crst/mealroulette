import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../api/client";
import { PersonalTelegramSettingsPage } from "./PersonalTelegramSettingsPage";

const fetchTelegramLink = vi.fn();
const fetchNotificationSubscription = vi.fn();
const createTelegramLinkToken = vi.fn();
const updateNotificationSubscription = vi.fn();

vi.mock("../../api/household", () => ({
  fetchTelegramLink: (...args: unknown[]) => fetchTelegramLink(...args),
  fetchNotificationSubscription: (...args: unknown[]) => fetchNotificationSubscription(...args),
  createTelegramLinkToken: (...args: unknown[]) => createTelegramLinkToken(...args),
  unlinkTelegram: vi.fn(),
  updateNotificationSubscription: (...args: unknown[]) => updateNotificationSubscription(...args),
  sendPersonalTelegramTest: vi.fn(),
  sendPersonalDailyReminder: vi.fn(),
}));

vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({
    accessToken: "token",
    hasHousehold: true,
  }),
}));

vi.mock("qrcode", () => ({
  default: {
    toDataURL: vi.fn(async () => "data:image/png;base64,qr"),
  },
}));

describe("PersonalTelegramSettingsPage", () => {
  beforeEach(() => {
    fetchTelegramLink.mockReset();
    fetchNotificationSubscription.mockReset();
    createTelegramLinkToken.mockReset();
    updateNotificationSubscription.mockReset();
  });

  it("loads link status and subscription toggles", async () => {
    fetchTelegramLink.mockResolvedValue({ linked: true, username: "me", display_name: "Me" });
    fetchNotificationSubscription.mockResolvedValue({
      notify_daily_reminder: true,
      notify_shopping: true,
      notify_roulette: false,
      daily_reminder_time: "08:00:00",
      shopping_window_days: 3,
      timezone: "Europe/Paris",
      last_reminder_sent_at: null,
    });

    render(
      <MemoryRouter>
        <PersonalTelegramSettingsPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText(/Linked as/i)).toBeInTheDocument();
    });
    expect(screen.getByLabelText("Daily reminder")).toBeChecked();
    expect(screen.getByLabelText("New roulette")).not.toBeChecked();
  });

  it("saves notification toggle and shows failure without implying success", async () => {
    fetchTelegramLink.mockResolvedValue({ linked: true, username: "me", display_name: "Me" });
    fetchNotificationSubscription.mockResolvedValue({
      notify_daily_reminder: true,
      notify_shopping: true,
      notify_roulette: true,
      daily_reminder_time: "08:00:00",
      shopping_window_days: 3,
      timezone: "Europe/Paris",
      last_reminder_sent_at: null,
    });
    updateNotificationSubscription.mockRejectedValue(new ApiError("Save failed", 500));

    render(
      <MemoryRouter>
        <PersonalTelegramSettingsPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByLabelText("New roulette")).toBeChecked();
    });

    fireEvent.click(screen.getByLabelText("New roulette"));

    await waitFor(() => {
      expect(updateNotificationSubscription).toHaveBeenCalledWith("token", { notify_roulette: false });
    });
    expect(await screen.findByRole("alert")).toHaveTextContent("Save failed");
    expect(screen.queryByText(/Notification preferences saved/i)).not.toBeInTheDocument();
  });
});
