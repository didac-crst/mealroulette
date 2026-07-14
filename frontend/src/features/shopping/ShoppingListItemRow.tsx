import type { ShoppingListItem, ShoppingSourceContribution } from "../../api/shopping";
import { formatQuantityWithUnit } from "../../lib/formatQuantity";
import { formatPlanDate } from "../planning/planFormat";

function formatSlotLabel(mealSlot: ShoppingSourceContribution["meal_slot"]): string {
  return mealSlot === "lunch" ? "Lunch" : "Dinner";
}

function formatUsageLine(contribution: ShoppingSourceContribution): string {
  const recipe = contribution.recipe_variant_name ? ` · ${contribution.recipe_variant_name}` : "";
  return `${formatPlanDate(contribution.date)} ${formatSlotLabel(contribution.meal_slot)} · ${contribution.dish_name}${recipe}`;
}

export type ShoppingListItemRowProps = {
  item: ShoppingListItem;
  showCheckbox: boolean;
  onToggle?: (checked: boolean) => void;
};

export function ShoppingListItemRow({ item, showCheckbox, onToggle }: ShoppingListItemRowProps) {
  const quantityLabel = formatQuantityWithUnit(item.quantity, item.unit_symbol);
  const approximatePrefix = item.approximate ? "~" : "";
  const usageCount = item.source_contributions.length;

  return (
    <div className={`shopping-list-item-row${item.checked ? " shopping-list-item-row-checked" : ""}`}>
      <div className="shopping-list-item-main">
        {showCheckbox && item.id != null ? (
          <input
            type="checkbox"
            className="shopping-list-item-checkbox"
            checked={item.checked}
            aria-label={`Mark ${item.display_name} as bought`}
            onChange={(event) => onToggle?.(event.target.checked)}
          />
        ) : (
          <span className="shopping-list-item-checkbox-spacer" aria-hidden />
        )}
        <div className="shopping-list-item-body">
          <div className="shopping-list-item-title-row">
            <span className={`shopping-list-item-name${item.checked ? " shopping-item-checked" : ""}`}>
              {item.display_name}
              {item.optional ? <span className="muted"> (optional)</span> : null}
            </span>
            <span className="shopping-list-item-quantity">
              {approximatePrefix}
              {quantityLabel}
            </span>
          </div>
          {usageCount > 0 ? (
            <div className="shopping-list-item-usage">
              <p className="muted shopping-list-item-usage-title">Needed for</p>
              <ul className="shopping-list-item-usage-list">
                {item.source_contributions.map((contribution) => (
                  <li key={`${contribution.meal_plan_item_id}-${contribution.quantity}`} className="muted">
                    {formatUsageLine(contribution)}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
