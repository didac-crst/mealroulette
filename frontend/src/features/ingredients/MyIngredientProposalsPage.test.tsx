import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MyIngredientProposalsPage } from "./MyIngredientProposalsPage";
import { useAuth } from "../auth/AuthContext";

const createIngredientProposal = vi.fn();
const listMyIngredientProposals = vi.fn();
const withdrawIngredientProposal = vi.fn();
const provideIngredientProposalInformation = vi.fn();

vi.mock("../../api/ingredientProposals", () => ({
  createIngredientProposal: (...args: unknown[]) => createIngredientProposal(...args),
  listMyIngredientProposals: (...args: unknown[]) => listMyIngredientProposals(...args),
  withdrawIngredientProposal: (...args: unknown[]) => withdrawIngredientProposal(...args),
  provideIngredientProposalInformation: (...args: unknown[]) =>
    provideIngredientProposalInformation(...args),
}));

vi.mock("../auth/AuthContext", () => ({
  useAuth: vi.fn(),
}));

type AuthStub = Partial<ReturnType<typeof useAuth>>;

function stubAuth(overrides: AuthStub = {}) {
  vi.mocked(useAuth).mockReturnValue({
    user: null,
    accessToken: "token",
    loading: false,
    login: vi.fn(),
    loginWithTelegramOtp: vi.fn(),
    refreshUser: vi.fn(),
    logout: vi.fn(),
    isPlatformAdmin: false,
    hasHousehold: true,
    isHouseholdAdmin: false,
    isAdmin: false,
    ...overrides,
  });
}

describe("MyIngredientProposalsPage", () => {
  beforeEach(() => {
    stubAuth();
    createIngredientProposal.mockReset();
    listMyIngredientProposals.mockReset();
    withdrawIngredientProposal.mockReset();
    provideIngredientProposalInformation.mockReset();
    listMyIngredientProposals.mockResolvedValue([]);
  });

  it("submits a member proposal and shows own proposals list", async () => {
    createIngredientProposal.mockResolvedValue({
      proposal: {
        id: "p1",
        proposed_name: "yuzu zest",
        resolution_status: "pending",
      },
      matches: [{ kind: "ingredient", label: "Yuzu" }],
    });
    listMyIngredientProposals
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([
        {
          id: "p1",
          proposed_name: "yuzu zest",
          resolution_status: "pending",
          review_note: null,
        },
      ]);

    render(
      <MemoryRouter>
        <MyIngredientProposalsPage />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Ingredient proposals" })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Proposed name"), { target: { value: "yuzu zest" } });
    fireEvent.change(screen.getByLabelText("Culinary context"), {
      target: { value: "Japanese pastry" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Submit proposal" }));

    await waitFor(() => {
      expect(createIngredientProposal).toHaveBeenCalledWith("token", {
        proposed_name: "yuzu zest",
        source_locale: "en",
        description: undefined,
        culinary_context: "Japanese pastry",
      });
    });
    expect(await screen.findByText("Proposal submitted for platform review.")).toBeInTheDocument();
    expect(await screen.findByText("yuzu zest")).toBeInTheDocument();
    expect(screen.getByText(/Ingredient:\s*Yuzu/i)).toBeInTheDocument();
    expect(screen.getByText(/This may already exist in the catalog/i)).toBeInTheDocument();
  });

  it("lets members provide information for needs_information proposals", async () => {
    listMyIngredientProposals
      .mockResolvedValueOnce([
        {
          id: "p2",
          proposed_name: "torch ginger",
          resolution_status: "needs_information",
          description: "old description",
          culinary_context: "old context",
          review_note: "Which part of the plant?",
        },
      ])
      .mockResolvedValueOnce([
        {
          id: "p2",
          proposed_name: "torch ginger",
          resolution_status: "pending",
          description: "Flower bud",
          culinary_context: "Laksa garnish",
          review_note: "Which part of the plant?\nSubmitter response: Fresh flower buds",
        },
      ]);
    provideIngredientProposalInformation.mockResolvedValue({
      id: "p2",
      resolution_status: "pending",
    });

    render(
      <MemoryRouter>
        <MyIngredientProposalsPage />
      </MemoryRouter>,
    );

    fireEvent.click(await screen.findByRole("button", { name: "My proposals" }));
    expect(await screen.findByText("torch ginger")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Provide information" }));

    fireEvent.change(screen.getByLabelText("Description"), { target: { value: "Flower bud" } });
    fireEvent.change(screen.getByLabelText("Culinary context"), {
      target: { value: "Laksa garnish" },
    });
    fireEvent.change(screen.getByLabelText("Response to reviewer"), {
      target: { value: "Fresh flower buds" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send information" }));

    await waitFor(() => {
      expect(provideIngredientProposalInformation).toHaveBeenCalledWith("token", "p2", {
        description: "Flower bud",
        culinary_context: "Laksa garnish",
        review_response: "Fresh flower buds",
      });
    });
    expect(await screen.findByText(/Information sent/i)).toBeInTheDocument();
  });

  it("sends empty strings when clearing description and context on provide-info", async () => {
    listMyIngredientProposals.mockResolvedValue([
      {
        id: "p3",
        proposed_name: "galangal",
        resolution_status: "needs_information",
        description: "old description",
        culinary_context: "old context",
        review_note: "Need more detail",
      },
    ]);
    provideIngredientProposalInformation.mockResolvedValue({
      id: "p3",
      resolution_status: "pending",
    });

    render(
      <MemoryRouter>
        <MyIngredientProposalsPage />
      </MemoryRouter>,
    );

    fireEvent.click(await screen.findByRole("button", { name: "My proposals" }));
    fireEvent.click(await screen.findByRole("button", { name: "Provide information" }));

    fireEvent.change(screen.getByLabelText("Description"), { target: { value: "" } });
    fireEvent.change(screen.getByLabelText("Culinary context"), { target: { value: "" } });
    fireEvent.change(screen.getByLabelText("Response to reviewer"), {
      target: { value: "See attached photo" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send information" }));

    await waitFor(() => {
      expect(provideIngredientProposalInformation).toHaveBeenCalledWith("token", "p3", {
        description: "",
        culinary_context: "",
        review_response: "See attached photo",
      });
    });
  });

  it("withdraws a pending proposal", async () => {
    listMyIngredientProposals
      .mockResolvedValueOnce([
        {
          id: "p4",
          proposed_name: "shiso leaf",
          resolution_status: "pending",
          review_note: null,
        },
      ])
      .mockResolvedValueOnce([]);
    withdrawIngredientProposal.mockResolvedValue({
      id: "p4",
      resolution_status: "withdrawn",
    });

    render(
      <MemoryRouter>
        <MyIngredientProposalsPage />
      </MemoryRouter>,
    );

    fireEvent.click(await screen.findByRole("button", { name: "My proposals" }));
    fireEvent.click(await screen.findByRole("button", { name: "Withdraw" }));

    await waitFor(() => {
      expect(withdrawIngredientProposal).toHaveBeenCalledWith("token", "p4");
    });
    expect(await screen.findByText("Proposal withdrawn.")).toBeInTheDocument();
  });

  it("withdraws a needs_information proposal", async () => {
    listMyIngredientProposals
      .mockResolvedValueOnce([
        {
          id: "p5",
          proposed_name: "kaffir lime",
          resolution_status: "needs_information",
          review_note: "Leaves or fruit?",
        },
      ])
      .mockResolvedValueOnce([]);
    withdrawIngredientProposal.mockResolvedValue({
      id: "p5",
      resolution_status: "withdrawn",
    });

    render(
      <MemoryRouter>
        <MyIngredientProposalsPage />
      </MemoryRouter>,
    );

    fireEvent.click(await screen.findByRole("button", { name: "My proposals" }));
    fireEvent.click(await screen.findByRole("button", { name: "Withdraw" }));

    await waitFor(() => {
      expect(withdrawIngredientProposal).toHaveBeenCalledWith("token", "p5");
    });
    expect(await screen.findByText("Proposal withdrawn.")).toBeInTheDocument();
  });

  it("shows household required empty state when user has no household", async () => {
    stubAuth({ hasHousehold: false });

    render(
      <MemoryRouter>
        <MyIngredientProposalsPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Household required")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Submit proposal" })).not.toBeInTheDocument();
    expect(listMyIngredientProposals).not.toHaveBeenCalled();
  });
});
