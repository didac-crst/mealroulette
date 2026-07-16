import { apiRequest } from "./client";

export type HouseholdRole = "household_admin" | "household_member";

export type Household = {
  id: string;
  name: string;
};

export type HouseholdMember = {
  membership_id: string;
  user_id: string;
  username: string;
  email: string;
  role: HouseholdRole;
  joined_at: string;
};

export type HouseholdInvitation = {
  id: string;
  expires_at: string;
  created_at: string;
  accepted_at: string | null;
};

export type HouseholdInvitationCreated = {
  invitation: HouseholdInvitation;
  invite_url: string;
};

export async function fetchHousehold(token: string): Promise<Household> {
  return apiRequest<Household>("/api/household", { token });
}

export async function updateHousehold(token: string, name: string): Promise<Household> {
  return apiRequest<Household>("/api/household", {
    method: "PATCH",
    token,
    body: JSON.stringify({ name }),
  });
}

export async function listHouseholdMembers(token: string): Promise<HouseholdMember[]> {
  return apiRequest<HouseholdMember[]>("/api/household/members", { token });
}

export async function updateMemberRole(
  token: string,
  membershipId: string,
  role: HouseholdRole,
): Promise<HouseholdMember> {
  return apiRequest<HouseholdMember>(`/api/household/members/${membershipId}`, {
    method: "PATCH",
    token,
    body: JSON.stringify({ role }),
  });
}

export async function removeHouseholdMember(token: string, membershipId: string): Promise<void> {
  await apiRequest<void>(`/api/household/members/${membershipId}`, {
    method: "DELETE",
    token,
  });
}

export async function createHouseholdInvitation(token: string): Promise<HouseholdInvitationCreated> {
  return apiRequest<HouseholdInvitationCreated>("/api/household/invitations", {
    method: "POST",
    token,
  });
}

export async function listHouseholdInvitations(token: string): Promise<HouseholdInvitation[]> {
  return apiRequest<HouseholdInvitation[]>("/api/household/invitations", { token });
}

export async function revokeHouseholdInvitation(token: string, invitationId: string): Promise<void> {
  await apiRequest<void>(`/api/household/invitations/${invitationId}`, {
    method: "DELETE",
    token,
  });
}

export async function acceptHouseholdInvitation(invitationToken: string, accessToken: string): Promise<void> {
  await apiRequest<void>("/api/household/invitations/accept", {
    method: "POST",
    token: accessToken,
    body: JSON.stringify({ token: invitationToken }),
  });
}
