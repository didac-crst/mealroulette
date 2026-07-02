import { Link } from "react-router-dom";

import type { Dish } from "../../api/catalog";
import { dishCardMeta, dishPlaceholderEmoji, truncateText } from "./dishVisual";

type Props = {
  dish: Dish;
};

export function DishCard({ dish }: Props) {
  const emoji = dishPlaceholderEmoji(dish);

  return (
    <Link to={`/dishes/${dish.id}`} className="dish-card">
      <div className="dish-card-media" aria-hidden={!dish.image_url}>
        {dish.image_url ? (
          <img src={dish.image_url} alt="" className="dish-card-image" loading="lazy" />
        ) : (
          <span className="dish-card-emoji">{emoji}</span>
        )}
      </div>
      <div className="dish-card-body">
        <h3 className="dish-card-title">{dish.name}</h3>
        {dish.description ? <p className="dish-card-description muted">{truncateText(dish.description, 100)}</p> : null}
        <p className="dish-card-meta muted">{dishCardMeta(dish)}</p>
      </div>
    </Link>
  );
}
