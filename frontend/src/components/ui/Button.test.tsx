import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Button } from "./Button";

describe("Button", () => {
  it("renders primary variant by default", () => {
    render(<Button>Save</Button>);
    const button = screen.getByRole("button", { name: "Save" });
    expect(button).toHaveClass("button");
    expect(button).not.toHaveClass("button-secondary");
  });

  it("renders semantic variants", () => {
    const { rerender } = render(<Button variant="roulette">Generate week</Button>);
    expect(screen.getByRole("button")).toHaveClass("button-roulette");

    rerender(<Button variant="danger">Delete</Button>);
    expect(screen.getByRole("button")).toHaveClass("button-danger");

    rerender(<Button variant="ghost">Undo</Button>);
    expect(screen.getByRole("button")).toHaveClass("button-ghost");
  });

  it("disables and marks busy while loading", () => {
    render(<Button loading>Signing in…</Button>);
    const button = screen.getByRole("button", { name: "Signing in…" });
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("aria-busy", "true");
    expect(button).toHaveClass("button-loading");
  });
});
