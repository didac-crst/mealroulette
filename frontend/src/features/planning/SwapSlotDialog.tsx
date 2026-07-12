import { useEffect, useRef } from "react";

import type { MealPlanItem } from "../../api/planning";
import { formatPlanDate, formatSlotLabel } from "./planFormat";

type Props = {
  item: MealPlanItem;
  targets: MealPlanItem[];
  busy: boolean;
  onClose: () => void;
  onConfirm: (targetItemId: number) => void;
};

export function SwapSlotDialog({ item, targets, busy, onClose, onConfirm }: Props) {
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    dialogRef.current?.focus();
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <div
        ref={dialogRef}
        className="modal-card stack"
        role="dialog"
        aria-modal="true"
        aria-labelledby="swap-slot-title"
        tabIndex={-1}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="row-between">
          <h3 id="swap-slot-title">Swap meal</h3>
          <button type="button" className="button button-secondary" onClick={onClose}>
            Cancel
          </button>
        </div>
        <p className="muted">
          Exchange <strong>{item.dish_name ?? "this slot"}</strong> ({formatPlanDate(item.date)} ·{" "}
          {formatSlotLabel(item.meal_slot)}) with:
        </p>
        {targets.length === 0 ? (
          <p className="muted">No other swappable slots this week.</p>
        ) : (
          <ul className="swap-target-list">
            {targets.map((target) => (
              <li key={target.id}>
                <button
                  type="button"
                  className="button button-secondary swap-target-button"
                  disabled={busy}
                  onClick={() => onConfirm(target.id)}
                >
                  <span>
                    {formatPlanDate(target.date)} · {formatSlotLabel(target.meal_slot)}
                  </span>
                  <span className="muted">{target.dish_name ?? "Empty slot"}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
