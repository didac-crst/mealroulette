import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  IngredientProposalReviewDetailPage,
  IngredientProposalReviewQueuePage,
} from "./IngredientProposalReviewPage";
import { ApiError } from "../../api/client";
import { AdminRoute } from "../../routes/AdminRoute";
import { useAuth } from "../auth/AuthContext";

const listPlatformIngredientProposals = vi.fn();
const getPlatformIngredientProposal = vi.fn();
const mapExistingIngredientProposal = vi.fn();
const addAliasIngredientProposal = vi.fn();
const approveNewIngredientProposal = vi.fn();
const fetchIngredients = vi.fn();
const fetchUnits = vi.fn();
const fetchFoodGroups = vi.fn();
const fetchFoodGroupFamilies = vi.fn();

const rejectIngredientProposal = vi.fn();
const requestIngredientProposalInformation = vi.fn();
const markDuplicateIngredientProposal = vi.fn();

vi.mock("../../api/ingredientProposals", () => ({
  listPlatformIngredientProposals: (...args: unknown[]) => listPlatformIngredientProposals(...args),
  getPlatformIngredientProposal: (...args: unknown[]) => getPlatformIngredientProposal(...args),
  mapExistingIngredientProposal: (...args: unknown[]) => mapExistingIngredientProposal(...args),
  addAliasIngredientProposal: (...args: unknown[]) => addAliasIngredientProposal(...args),
  approveNewIngredientProposal: (...args: unknown[]) => approveNewIngredientProposal(...args),
  rejectIngredientProposal: (...args: unknown[]) => rejectIngredientProposal(...args),
  requestIngredientProposalInformation: (...args: unknown[]) =>
    requestIngredientProposalInformation(...args),
  markDuplicateIngredientProposal: (...args: unknown[]) => markDuplicateIngredientProposal(...args),
}));

vi.mock("../../api/catalog", () => ({
  fetchIngredients: (...args: unknown[]) => fetchIngredients(...args),
  fetchUnits: (...args: unknown[]) => fetchUnits(...args),
}));

vi.mock("../../api/taxonomy", () => ({
  fetchFoodGroups: (...args: unknown[]) => fetchFoodGroups(...args),
  fetchFoodGroupFamilies: (...args: unknown[]) => fetchFoodGroupFamilies(...args),
}));

vi.mock("../auth/AuthContext", () => ({
  useAuth: vi.fn(),
}));

type AuthStub = Partial<ReturnType<typeof useAuth>>;

function stubAuth(overrides: AuthStub = {}) {
  vi.mocked(useAuth).mockReturnValue({
    user: { id: "1", username: "admin" } as ReturnType<typeof useAuth>["user"],
    accessToken: "token",
    loading: false,
    login: vi.fn(),
    loginWithTelegramOtp: vi.fn(),
    refreshUser: vi.fn(),
    logout: vi.fn(),
    isPlatformAdmin: true,
    hasHousehold: true,
    isHouseholdAdmin: false,
    isAdmin: true,
    ...overrides,
  });
}

const pendingProposal = {
  id: "p1",
  proposed_name: "yuzu zest",
  normalized_name: "yuzu zest",
  suggested_canonical_name: "yuzu_zest",
  resolution_status: "pending",
  source_locale: "en",
  description: null,
  culinary_context: null,
  suggested_food_group_id: null,
  suggested_family_id: null,
  review_note: null,
};

function renderDetailPage(proposalId = "p1") {
  return render(
    <MemoryRouter initialEntries={[`/ingredients/proposal-review/${proposalId}`]}>
      <Routes>
        <Route path="/ingredients/proposal-review/:proposalId" element={<IngredientProposalReviewDetailPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

async function selectExistingIngredient(label = "Yuzu") {
  const input = await screen.findByLabelText("Existing ingredient");
  fireEvent.focus(input);
  fireEvent.change(input, { target: { value: label } });
  fireEvent.click(await screen.findByRole("option", { name: /Yuzu \(yuzu\) · #42/i }));
}

describe("Ingredient proposal review", () => {
  beforeEach(() => {
    stubAuth();
    listPlatformIngredientProposals.mockReset();
    getPlatformIngredientProposal.mockReset();
    mapExistingIngredientProposal.mockReset();
    addAliasIngredientProposal.mockReset();
    approveNewIngredientProposal.mockReset();
    rejectIngredientProposal.mockReset();
    requestIngredientProposalInformation.mockReset();
    markDuplicateIngredientProposal.mockReset();
    fetchIngredients.mockReset();
    fetchUnits.mockReset();
    fetchFoodGroups.mockReset();
    fetchFoodGroupFamilies.mockReset();
    listPlatformIngredientProposals.mockResolvedValue([
      {
        id: "p1",
        proposed_name: "yuzu zest",
        resolution_status: "pending",
        source_locale: "en",
        source_type: "manual",
      },
    ]);
    getPlatformIngredientProposal.mockResolvedValue(pendingProposal);
    fetchUnits.mockResolvedValue([]);
    fetchFoodGroups.mockResolvedValue([]);
    fetchFoodGroupFamilies.mockResolvedValue([]);
    fetchIngredients.mockResolvedValue([
      {
        id: 42,
        display_name: "Yuzu",
        canonical_name: "yuzu",
      },
    ]);
  });

  it("lets platform admins open the review queue", async () => {
    render(
      <MemoryRouter initialEntries={["/ingredients/proposal-review"]}>
        <Routes>
          <Route element={<AdminRoute />}>
            <Route path="/ingredients/proposal-review" element={<IngredientProposalReviewQueuePage />} />
          </Route>
          <Route path="/today" element={<p>Today page</p>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Ingredient proposal review" })).toBeInTheDocument();
    await waitFor(() => {
      expect(listPlatformIngredientProposals).toHaveBeenCalledWith("token", "pending");
    });
    expect(screen.getByText("yuzu zest")).toBeInTheDocument();
  });

  it("denies non-platform admins", async () => {
    stubAuth({
      user: { id: "2", username: "member" } as ReturnType<typeof useAuth>["user"],
      accessToken: "token",
      isPlatformAdmin: false,
      hasHousehold: true,
      isAdmin: false,
    });

    render(
      <MemoryRouter initialEntries={["/ingredients/proposal-review"]}>
        <Routes>
          <Route element={<AdminRoute />}>
            <Route path="/ingredients/proposal-review" element={<IngredientProposalReviewQueuePage />} />
          </Route>
          <Route path="/today" element={<p>Today page</p>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText("Today page")).toBeInTheDocument();
    expect(listPlatformIngredientProposals).not.toHaveBeenCalled();
  });

  it("uses ingredient search/select instead of a raw ID field", async () => {
    mapExistingIngredientProposal.mockResolvedValue({
      id: "p1",
      resolution_status: "approved",
      resolution_type: "mapped_existing",
    });

    renderDetailPage();

    expect(await screen.findByLabelText("Existing ingredient")).toBeInTheDocument();
    expect(screen.queryByLabelText(/Existing ingredient ID/i)).not.toBeInTheDocument();
    expect(screen.getByLabelText("Alias text")).toBeInTheDocument();
    expect(screen.getByLabelText(/Language/i)).toBeInTheDocument();

    await selectExistingIngredient();
    fireEvent.click(screen.getByRole("button", { name: "Map existing" }));

    await waitFor(() => {
      expect(mapExistingIngredientProposal).toHaveBeenCalledWith("token", "p1", {
        ingredient_id: 42,
        review_note: undefined,
      });
    });
  });

  it("requires a review note before reject, request information, and mark duplicate", async () => {
    renderDetailPage();

    expect(await screen.findByLabelText("Review note")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Reject" }));
    expect(
      await screen.findByText(/Add a review note explaining why or what the submitter should do next/i),
    ).toBeInTheDocument();
    expect(rejectIngredientProposal).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Request information" }));
    expect(requestIngredientProposalInformation).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Mark duplicate" }));
    expect(markDuplicateIngredientProposal).not.toHaveBeenCalled();

    fireEvent.change(screen.getByLabelText("Review note"), {
      target: { value: "Needs a clearer culinary use" },
    });
    rejectIngredientProposal.mockResolvedValue({
      id: "p1",
      resolution_status: "rejected",
      resolution_type: "rejected",
    });
    fireEvent.click(screen.getByRole("button", { name: "Reject" }));

    await waitFor(() => {
      expect(rejectIngredientProposal).toHaveBeenCalledWith(
        "token",
        "p1",
        "Needs a clearer culinary use",
      );
    });
  });

  it("sends add-alias payload with selected ingredient, alias, and language", async () => {
    addAliasIngredientProposal.mockResolvedValue({
      id: "p1",
      resolution_status: "approved",
      resolution_type: "added_alias",
    });

    renderDetailPage();

    await selectExistingIngredient();
    fireEvent.change(screen.getByLabelText("Alias text"), { target: { value: "yuzu peel" } });
    fireEvent.change(screen.getByLabelText(/Language/i), { target: { value: "ja" } });
    fireEvent.change(screen.getByLabelText("Review note"), { target: { value: "Alias for Japanese locale" } });
    fireEvent.click(screen.getByRole("button", { name: "Add alias" }));

    await waitFor(() => {
      expect(addAliasIngredientProposal).toHaveBeenCalledWith("token", "p1", {
        ingredient_id: 42,
        alias: "yuzu peel",
        language: "ja",
        review_note: "Alias for Japanese locale",
      });
    });
  });

  it("sends approve-new payload with required taxonomy fields", async () => {
    fetchFoodGroups.mockResolvedValue([{ id: "vegetables", label: "Vegetables" }]);
    fetchFoodGroupFamilies.mockResolvedValue([{ id: "citrus", label: "Citrus" }]);

    approveNewIngredientProposal.mockResolvedValue({
      id: "p1",
      resolution_status: "approved",
      resolution_type: "approved_new",
    });

    renderDetailPage();

    expect(await screen.findByLabelText("Canonical name")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Canonical name"), { target: { value: "yuzu_zest" } });
    fireEvent.change(screen.getByLabelText("Display name"), { target: { value: "Yuzu zest" } });
    fireEvent.change(screen.getByLabelText("Aliases"), { target: { value: "yuzu peel\nyuzu rind" } });

    fireEvent.change(screen.getByLabelText("Food group"), { target: { value: "vegetables" } });
    await waitFor(() => {
      expect(fetchFoodGroupFamilies).toHaveBeenCalledWith("token", "vegetables");
    });
    await waitFor(() => {
      expect(screen.getByRole("option", { name: "Citrus" })).toBeInTheDocument();
    });
    fireEvent.change(screen.getByLabelText("Family"), { target: { value: "citrus" } });

    fireEvent.click(screen.getByRole("button", { name: "Approve new canonical" }));

    await waitFor(() => {
      expect(approveNewIngredientProposal).toHaveBeenCalledWith("token", "p1", {
        canonical_name: "yuzu_zest",
        display_name: "Yuzu zest",
        aliases: ["yuzu peel", "yuzu rind"],
        food_group: "vegetables",
        family: "citrus",
        storage_class: undefined,
        product_form: undefined,
        preservation: undefined,
        default_unit_id: undefined,
        preferred_shopping_unit_id: undefined,
        conversion_notes: undefined,
        review_note: undefined,
      });
    });
  });

  it("sends request-information payload with review note", async () => {
    requestIngredientProposalInformation.mockResolvedValue({
      id: "p1",
      resolution_status: "needs_information",
    });

    renderDetailPage();

    fireEvent.change(await screen.findByLabelText("Review note"), {
      target: { value: "Which part of the plant?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Request information" }));

    await waitFor(() => {
      expect(requestIngredientProposalInformation).toHaveBeenCalledWith(
        "token",
        "p1",
        "Which part of the plant?",
      );
    });
  });

  it("sends mark-duplicate payload with review note and optional ingredient", async () => {
    markDuplicateIngredientProposal.mockResolvedValue({
      id: "p1",
      resolution_status: "duplicate",
    });

    renderDetailPage();

    await selectExistingIngredient();
    fireEvent.change(screen.getByLabelText("Review note"), {
      target: { value: "Already covered by Yuzu" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Mark duplicate" }));

    await waitFor(() => {
      expect(markDuplicateIngredientProposal).toHaveBeenCalledWith("token", "p1", {
        ingredient_id: 42,
        review_note: "Already covered by Yuzu",
      });
    });
  });

  it("shows map-existing API errors without leaving the page stuck", async () => {
    mapExistingIngredientProposal.mockRejectedValue(new ApiError("Ingredient not found", 404));

    renderDetailPage();

    await selectExistingIngredient();
    fireEvent.click(screen.getByRole("button", { name: "Map existing" }));

    expect(await screen.findByText("Ingredient not found")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Map existing" })).not.toBeDisabled();
    expect(getPlatformIngredientProposal).toHaveBeenCalledTimes(1);
  });

  it("clears previous proposals when queue filter request fails", async () => {
    render(
      <MemoryRouter initialEntries={["/ingredients/proposal-review"]}>
        <Routes>
          <Route path="/ingredients/proposal-review" element={<IngredientProposalReviewQueuePage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText("yuzu zest")).toBeInTheDocument();

    listPlatformIngredientProposals.mockRejectedValue(new ApiError("Filter failed", 500));

    fireEvent.change(screen.getByLabelText("Status filter"), { target: { value: "rejected" } });

    await waitFor(() => {
      expect(listPlatformIngredientProposals).toHaveBeenCalledWith("token", "rejected");
    });
    expect(await screen.findByText("Filter failed")).toBeInTheDocument();
    expect(screen.queryByText("yuzu zest")).not.toBeInTheDocument();
  });

  it("shows options error when review option loading fails", async () => {
    fetchIngredients.mockRejectedValue(new ApiError("Catalog unavailable", 503));

    renderDetailPage();

    expect(await screen.findByText("Catalog unavailable")).toBeInTheDocument();
  });

  it("ignores stale family responses after switching food groups", async () => {
    fetchFoodGroups.mockResolvedValue([
      { id: "group-a", label: "Group A" },
      { id: "group-b", label: "Group B" },
    ]);

    let resolveGroupA: (value: { id: string; label: string }[]) => void = () => {};
    const groupAPromise = new Promise<{ id: string; label: string }[]>((resolve) => {
      resolveGroupA = resolve;
    });

    fetchFoodGroupFamilies.mockImplementation((_token: string, groupId: string) => {
      if (groupId === "group-a") {
        return groupAPromise;
      }
      return Promise.resolve([{ id: "family-b", label: "Family B" }]);
    });

    renderDetailPage();

    expect(await screen.findByLabelText("Food group")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Food group"), { target: { value: "group-a" } });
    fireEvent.change(screen.getByLabelText("Food group"), { target: { value: "group-b" } });

    await waitFor(() => {
      expect(screen.getByRole("option", { name: "Family B" })).toBeInTheDocument();
    });

    resolveGroupA([{ id: "family-a", label: "Family A" }]);

    await waitFor(() => {
      expect(fetchFoodGroupFamilies).toHaveBeenCalledWith("token", "group-a");
    });

    expect(screen.queryByRole("option", { name: "Family A" })).not.toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Family B" })).toBeInTheDocument();
  });
});
