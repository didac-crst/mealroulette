import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { useDialogA11y } from "./useDialogA11y";

function TestDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const dialogRef = useDialogA11y(open, onClose);

  return (
    <>
      <button type="button">Trigger</button>
      {open ? (
        <div ref={dialogRef} role="dialog" aria-modal="true" tabIndex={-1}>
          <button type="button">First</button>
          <button type="button">Second</button>
        </div>
      ) : null}
    </>
  );
}

describe("useDialogA11y", () => {
  it("focuses the first focusable element when opened", () => {
    render(<TestDialog open onClose={vi.fn()} />);

    expect(screen.getByRole("button", { name: "First" })).toHaveFocus();
  });

  it("calls onClose when Escape is pressed", () => {
    const onClose = vi.fn();
    render(<TestDialog open onClose={onClose} />);

    fireEvent.keyDown(document, { key: "Escape" });

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("restores focus to the trigger when closed", async () => {
    const onClose = vi.fn();
    const { rerender } = render(<TestDialog open={false} onClose={onClose} />);
    const trigger = screen.getByRole("button", { name: "Trigger" });
    trigger.focus();

    rerender(<TestDialog open onClose={onClose} />);
    rerender(<TestDialog open={false} onClose={onClose} />);

    await waitFor(() => {
      expect(trigger).toHaveFocus();
    });
  });
});
