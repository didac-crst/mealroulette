import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "./App";

describe("App", () => {
  it("renders the application shell", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "MealRoulette" })).toBeInTheDocument();
    expect(screen.getByLabelText("API health status")).toBeInTheDocument();
    expect(screen.getByTestId("health-status")).toHaveTextContent("Status: checking...");
  });
});
