import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import * as householdApi from "../../api/household";
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
    refreshUser: vi.fn(),
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

describe("HouseholdMembersPage", () => {
  it("loads household members and creates invite links", async () => {
    vi.mocked(householdApi.fetchHousehold).mockResolvedValue({ id: "household-1", name: "Casa" });
    vi.mocked(householdApi.listHouseholdMembers).mockResolvedValue(members);
    vi.mocked(householdApi.listHouseholdInvitations).mockResolvedValue([]);
    vi.mocked(householdApi.createHouseholdInvitation).mockResolvedValue({
      invitation: {
        id: "invitation-1",
        created_at: "2026-07-16T00:00:00Z",
        expires_at: "2026-07-23T00:00:00Z",
        accepted_at: null,
      },
      invite_url: "/join?token=invite-token",
    });

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
  });
});
