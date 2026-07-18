import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  IngredientProposalReviewDetailPage,
  IngredientProposalReviewQueuePage,
} from "./IngredientProposalReviewPage";
import { AdminRoute } from "../../routes/AdminRoute";
import { useAuth } from "../auth/AuthContext";

const listPlatformIngredientProposals = vi.fn();
const getPlatformIngredientProposal = vi.fn();
const mapExistingIngredientProposal = vi.fn();
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
  addAliasIngredientProposal: vi.fn(),
  approveNewIngredientProposal: vi.fn(),
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

function stubAuth(overrides: AuthStub) {
  vi.mocked(useAuth).mockReturnValue({
    user: null,
    accessToken: null,
    loading: false,
    login: vi.fn(),
    loginWithTelegramOtp: vi.fn(),
    refreshUser: vi.fn(),
    logout: vi.fn(),
    isPlatformAdmin: false,
    hasHousehold: false,
    isHouseholdAdmin: false,
    isAdmin: false,
    ...overrides,
  });
}

describe("Ingredient proposal review", () => {
  beforeEach(() => {
    listPlatformIngredientProposals.mockReset();
    getPlatformIngredientProposal.mockReset();
    mapExistingIngredientProposal.mockReset();
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
    stubAuth({
      user: { id: "1", username: "admin" } as ReturnType<typeof useAuth>["user"],
      accessToken: "token",
      isPlatformAdmin: true,
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
    stubAuth({
      user: { id: "1", username: "admin" } as ReturnType<typeof useAuth>["user"],
      accessToken: "token",
      isPlatformAdmin: true,
    });
    getPlatformIngredientProposal.mockResolvedValue({
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
    });
    mapExistingIngredientProposal.mockResolvedValue({
      id: "p1",
      resolution_status: "approved",
      resolution_type: "mapped_existing",
    });

    render(
      <MemoryRouter initialEntries={["/ingredients/proposal-review/p1"]}>
        <Routes>
          <Route path="/ingredients/proposal-review/:proposalId" element={<IngredientProposalReviewDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByLabelText("Existing ingredient")).toBeInTheDocument();
    expect(screen.queryByLabelText(/Existing ingredient ID/i)).not.toBeInTheDocument();
    expect(screen.getByLabelText("Alias text")).toBeInTheDocument();
    expect(screen.getByLabelText(/Language/i)).toBeInTheDocument();

    fireEvent.focus(screen.getByLabelText("Existing ingredient"));
    fireEvent.change(screen.getByLabelText("Existing ingredient"), { target: { value: "Yuzu" } });
    fireEvent.click(await screen.findByRole("option", { name: /Yuzu \(yuzu\) · #42/i }));
    fireEvent.click(screen.getByRole("button", { name: "Map existing" }));

    await waitFor(() => {
      expect(mapExistingIngredientProposal).toHaveBeenCalledWith("token", "p1", {
        ingredient_id: 42,
        review_note: undefined,
      });
    });
  });

  it("requires a review note before reject, request information, and mark duplicate", async () => {
    getPlatformIngredientProposal.mockResolvedValue({
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
    });

    render(
      <MemoryRouter initialEntries={["/ingredients/proposal-review/p1"]}>
        <Routes>
          <Route path="/ingredients/proposal-review/:proposalId" element={<IngredientProposalReviewDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

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
});
