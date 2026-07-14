import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StatusBadge } from "./StatusBadge";

describe("StatusBadge", () => {
  it("renders label with variant class", () => {
    render(<StatusBadge variant="success">Ate as planned</StatusBadge>);
    const badge = screen.getByText("Ate as planned");
    expect(badge).toHaveClass("status-badge", "status-badge-success");
  });
});
