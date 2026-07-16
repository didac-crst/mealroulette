import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as householdApi from "../../api/household";
import { ApiError } from "../../api/client";
import { HouseholdMembersPage } from "./HouseholdMembersPage";

vi.mock("../../api/household", () => ({
  fetchHousehold: vi.fn(),
  updateHousehold: vi.fn(),
  listHouseholdMembers: vi.fn(),
  updateMemberRole: vi.fn(),
  removeHouseholdMember: vi.fn(),
  createHouseholdInvitation: vi.fn(),
  listHouseholdInvitations: vi.fn(),
  revokeHouseholdInvitation: vi.fn(),
}));

vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({
    accessToken: "access-token",
    user: { id: "user-1", username: "didac" },
    isHouseholdAdmin: true,
    loading: false,
    refreshUser: vi.fn().mockResolvedValue(undefined),
  }),
}));

vi.mock("../../lib/copyTextToClipboard", () => ({
  copyTextToClipboard: vi.fn().mockResolvedValue(true),
}));

const members = [
  {
    membership_id: "membership-1",
    user_id: "user-1",
    username: "didac",
    email: "didac@example.com",
    role: "household_admin" as const,
    joined_at: "2026-07-16T00:00:00Z",
  },
  {
    membership_id: "membership-2",
    user_id: "user-2",
    username: "guest",
    email: "guest@example.com",
    role: "household_member" as const,
    joined_at: "2026-07-16T00:00:00Z",
  },
];

const createdInvitation = {
  id: "invitation-1",
  created_at: "2026-07-16T00:00:00Z",
  expires_at: "2026-07-23T00:00:00Z",
  accepted_at: null,
};

describe("HouseholdMembersPage", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
    vi.mocked(householdApi.fetchHousehold).mockResolvedValue({ id: "household-1", name: "Casa" });
    vi.mocked(householdApi.listHouseholdMembers).mockResolvedValue(members);
    vi.mocked(householdApi.listHouseholdInvitations).mockResolvedValue([]);
  });

  it("loads household members and shows a created invite link", async () => {
    vi.mocked(householdApi.createHouseholdInvitation).mockResolvedValue({
      invitation: createdInvitation,
      invite_url: "/join?token=invite-token",
    });
    vi.mocked(householdApi.listHouseholdInvitations)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([createdInvitation]);

    render(
      <MemoryRouter>
        <HouseholdMembersPage />
      </MemoryRouter>,
    );

    expect(await screen.findByDisplayValue("Casa")).toBeInTheDocument();
    expect(screen.getByText("guest")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Create invite link" }));

    await waitFor(() => {
      expect(householdApi.createHouseholdInvitation).toHaveBeenCalledWith("access-token");
    });
    expect(await screen.findByText(/\/join\?token=invite-token/)).toBeInTheDocument();
    expect(screen.getByText("Invitation link created.")).toBeInTheDocument();
  });

  it("shows create-invitation API failures", async () => {
    vi.mocked(householdApi.createHouseholdInvitation).mockRejectedValue(new ApiError("Forbidden", 403));

    render(
      <MemoryRouter>
        <HouseholdMembersPage />
      </MemoryRouter>,
    );

    expect(await screen.findByDisplayValue("Casa")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Create invite link" }));

    expect(await screen.findByText("Forbidden")).toBeInTheDocument();
  });
});
