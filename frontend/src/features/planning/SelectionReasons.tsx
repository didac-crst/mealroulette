import type { MealPlanItem } from "../../api/planning";
import { selectionReasonsList } from "./planFormat";

type Props = {
  item: MealPlanItem;
};

export function SelectionReasons({ item }: Props) {
  const reasons = selectionReasonsList(item);
  if (reasons.length === 0) {
    return null;
  }

  return (
    <div className="selection-reasons">
      <p className="selection-reasons-title muted">Why this meal</p>
      <ul className="selection-reasons-list">
        {reasons.map((reason) => (
          <li key={reason}>{reason}</li>
        ))}
      </ul>
    </div>
  );
}
