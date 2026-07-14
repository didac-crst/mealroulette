import type { MealPlanItem } from "../../api/planning";
import { DisclosureSection } from "../../components/ui";
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
    <DisclosureSection title="Why this meal">
      <ul className="selection-reasons-list">
        {reasons.map((reason, index) => (
          <li key={`${index}-${reason}`}>{reason}</li>
        ))}
      </ul>
    </DisclosureSection>
  );
}
