import type { RecipeIngredient, Unit } from "../../api/catalog";
import { formatQuantityWithUnit } from "../../lib/formatQuantity";

export type CookingIngredientListProps = {
  items: RecipeIngredient[];
  ingredientNames: Record<number, string>;
  units: Unit[];
  className?: string;
};

export function CookingIngredientList({
  items,
  ingredientNames,
  units,
  className,
}: CookingIngredientListProps) {
  if (items.length === 0) {
    return <p className="muted">No ingredients listed.</p>;
  }

  return (
    <ul className={["cooking-ingredient-list", className].filter(Boolean).join(" ")}>
      {items.map((item) => {
        const name = ingredientNames[item.ingredient_id] ?? `ingredient #${item.ingredient_id}`;
        const unitSymbol = units.find((unit) => unit.id === item.unit_id)?.symbol;
        const quantity = formatQuantityWithUnit(item.quantity, unitSymbol);
        return (
          <li key={item.id} className="cooking-ingredient-row">
            <span className="cooking-ingredient-name">
              {name}
              {item.optional ? <span className="muted"> (optional)</span> : null}
            </span>
            {quantity ? <span className="cooking-ingredient-quantity">{quantity}</span> : null}
          </li>
        );
      })}
    </ul>
  );
}
