import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { RecipeCompositionChart } from "./RecipeCompositionChart";

describe("RecipeCompositionChart", () => {
  it("groups minor slices into Other in the legend", () => {
    render(
      <RecipeCompositionChart
        traits={{
          food_group_weights: {
            carbohydrate: 82,
            cheese: 8,
            vegetable: 6,
            fruit: 4,
          },
        }}
      />,
    );

    expect(screen.getByText("Carbohydrate")).toBeInTheDocument();
    expect(screen.getByText("82%")).toBeInTheDocument();
    expect(screen.getByText("Other")).toBeInTheDocument();
    expect(screen.getByText("18%")).toBeInTheDocument();
  });

  it("renders the empty state when there are no weights", () => {
    render(<RecipeCompositionChart traits={{ food_group_weights: {} }} />);

    expect(screen.getByText(/No composition yet/i)).toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  it("exposes an accessible chart name and text summary", () => {
    render(
      <RecipeCompositionChart
        traits={{
          food_group_weights: {
            carbohydrate: 90,
            cheese: 10,
          },
        }}
      />,
    );

    expect(screen.getByRole("img", { name: /Food group composition/i })).toBeInTheDocument();
    expect(screen.getByText(/Carbohydrate 90%, Cheese 10%/i)).toBeInTheDocument();
  });
});
