import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { FormSaveStatus } from "./FormSaveStatus";

describe("FormSaveStatus", () => {
  it("renders nothing when idle", () => {
    const { container } = render(<FormSaveStatus status="idle" />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders unsaved and saving labels", () => {
    const { rerender } = render(<FormSaveStatus status="unsaved" />);
    expect(screen.getByRole("status")).toHaveTextContent("Unsaved changes");
    expect(screen.getByRole("status")).toHaveClass("form-save-status-unsaved");

    rerender(<FormSaveStatus status="saving" />);
    expect(screen.getByRole("status")).toHaveTextContent("Saving…");
    expect(screen.getByRole("status")).toHaveClass("form-save-status-saving");
  });

  it("renders error message with alert role", () => {
    render(<FormSaveStatus status="error" errorMessage="Name is required" />);
    expect(screen.getByRole("alert")).toHaveTextContent("Name is required");
    expect(screen.getByRole("alert")).toHaveClass("form-save-status-error");
  });
});
