import { apiRequest } from "./client";

export type IngredientProposalSourceType =
  | "manual"
  | "recipe_editor"
  | "recipe_import"
  | "llm_recipe_import"
  | "bulk_import"
  | "platform_admin";

export type IngredientProposalResolutionStatus =
  | "pending"
  | "needs_information"
  | "duplicate"
  | "approved"
  | "rejected"
  | "withdrawn";

export type IngredientProposalResolutionType =
  | "created_canonical"
  | "mapped_existing"
  | "added_alias"
  | "rejected";

export type IngredientProposalMatch = {
  kind: "ingredient" | "alias" | "pending_proposal";
  label: string;
  ingredient_id?: number | null;
  proposal_id?: string | null;
  alias?: string | null;
};

export type IngredientProposal = {
  id: string;
  proposed_name: string;
  normalized_name: string;
  source_locale: string;
  description: string | null;
  culinary_context: string | null;
  suggested_food_group_id: string | null;
  suggested_family_id: string | null;
  suggested_storage_class: string | null;
  suggested_product_form: string | null;
  suggested_preservation: string | null;
  resolution_status: IngredientProposalResolutionStatus;
  resolution_type: IngredientProposalResolutionType | null;
  resolved_ingredient_id: number | null;
  proposed_by_user_id: string;
  household_id: string | null;
  source_type: IngredientProposalSourceType;
  source_reference_type: string | null;
  source_reference_id: string | null;
  reviewed_by_user_id: string | null;
  reviewed_at: string | null;
  review_note: string | null;
  created_at: string;
  updated_at: string;
  suggested_canonical_name?: string | null;
};

export type IngredientProposalCreateResponse = {
  proposal: IngredientProposal;
  matches: IngredientProposalMatch[];
};

export type IngredientProposalCreatePayload = {
  proposed_name: string;
  source_locale?: string;
  description?: string;
  culinary_context?: string;
  suggested_food_group_id?: string;
  suggested_family_id?: string;
  source_type?: IngredientProposalSourceType;
};

export function createIngredientProposal(token: string, payload: IngredientProposalCreatePayload) {
  return apiRequest<IngredientProposalCreateResponse>("/api/ingredient-proposals", {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  });
}

export function listMyIngredientProposals(token: string) {
  return apiRequest<IngredientProposal[]>("/api/ingredient-proposals/mine", { token });
}

export function withdrawIngredientProposal(token: string, proposalId: string) {
  return apiRequest<IngredientProposal>(`/api/ingredient-proposals/${proposalId}/withdraw`, {
    method: "POST",
    token,
  });
}

export function provideIngredientProposalInformation(
  token: string,
  proposalId: string,
  payload: {
    description?: string;
    culinary_context?: string;
    review_response?: string;
  },
) {
  return apiRequest<IngredientProposal>(`/api/ingredient-proposals/${proposalId}/provide-information`, {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  });
}

export function listPlatformIngredientProposals(token: string, resolutionStatus?: string) {
  const query = resolutionStatus ? `?resolution_status=${encodeURIComponent(resolutionStatus)}` : "";
  return apiRequest<IngredientProposal[]>(`/api/platform/ingredient-proposals${query}`, { token });
}

export function getPlatformIngredientProposal(token: string, proposalId: string) {
  return apiRequest<IngredientProposal>(`/api/platform/ingredient-proposals/${proposalId}`, { token });
}

export function mapExistingIngredientProposal(
  token: string,
  proposalId: string,
  payload: { ingredient_id: number; review_note?: string },
) {
  return apiRequest<IngredientProposal>(`/api/platform/ingredient-proposals/${proposalId}/map-existing`, {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  });
}

export function addAliasIngredientProposal(
  token: string,
  proposalId: string,
  payload: { ingredient_id: number; alias?: string; language?: string; review_note?: string },
) {
  return apiRequest<IngredientProposal>(`/api/platform/ingredient-proposals/${proposalId}/add-alias`, {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  });
}

export function approveNewIngredientProposal(
  token: string,
  proposalId: string,
  payload: {
    canonical_name?: string;
    display_name?: string;
    aliases?: string[];
    food_group?: string;
    family?: string;
    storage_class?: string;
    culinary_category?: string;
    product_form?: string;
    preservation?: string;
    default_unit_id?: number;
    preferred_shopping_unit_id?: number;
    notes?: string;
    conversion_notes?: string;
    review_note?: string;
  },
) {
  return apiRequest<IngredientProposal>(`/api/platform/ingredient-proposals/${proposalId}/approve-new`, {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  });
}

export function rejectIngredientProposal(token: string, proposalId: string, reviewNote: string) {
  return apiRequest<IngredientProposal>(`/api/platform/ingredient-proposals/${proposalId}/reject`, {
    method: "POST",
    token,
    body: JSON.stringify({ review_note: reviewNote }),
  });
}

export function requestIngredientProposalInformation(
  token: string,
  proposalId: string,
  reviewNote: string,
) {
  return apiRequest<IngredientProposal>(
    `/api/platform/ingredient-proposals/${proposalId}/request-information`,
    {
      method: "POST",
      token,
      body: JSON.stringify({ review_note: reviewNote }),
    },
  );
}

export function markDuplicateIngredientProposal(
  token: string,
  proposalId: string,
  payload: { review_note: string; ingredient_id?: number },
) {
  return apiRequest<IngredientProposal>(`/api/platform/ingredient-proposals/${proposalId}/mark-duplicate`, {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  });
}
