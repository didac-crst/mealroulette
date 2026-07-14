import { BottomSheet, ChoiceCard } from "../../components/ui";
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
  return (
    <BottomSheet open titleId="swap-slot-title" onClose={onClose}>
      <div className="bottom-sheet-content stack">
        <h3 id="swap-slot-title">Swap meal</h3>
        <p className="muted">
          Exchange <strong>{item.title ?? item.dish_name ?? "this slot"}</strong> ({formatPlanDate(item.date)} ·{" "}
          {formatSlotLabel(item.meal_slot)}) with:
        </p>
        {targets.length === 0 ? (
          <p className="muted">No other swappable slots this week.</p>
        ) : (
          <div className="swap-target-grid" role="list">
            {targets.map((target) => (
              <ChoiceCard
                key={target.id}
                title={`${formatPlanDate(target.date)} · ${formatSlotLabel(target.meal_slot)}`}
                description={target.title ?? target.dish_name ?? "Empty slot"}
                disabled={busy}
                onClick={() => onConfirm(target.id)}
              />
            ))}
          </div>
        )}
      </div>
    </BottomSheet>
  );
}
