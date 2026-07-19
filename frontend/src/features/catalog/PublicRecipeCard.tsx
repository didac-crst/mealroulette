import { Link } from "react-router-dom";

import type { PublicRecipeMember } from "../../api/publicCatalog";
import {
  publicCatalogCardDescription,
  publicCatalogCardMeta,
} from "./publicCatalogDiscovery";

type Props = {
  item: PublicRecipeMember;
};

export function PublicRecipeCard({ item }: Props) {
  const description = publicCatalogCardDescription(item);

  return (
    <article className="dish-card">
      <Link to={`/catalog/recipes/${item.id}`} className="dish-card-link">
        <div className="dish-card-media" aria-hidden="true">
          <span className="dish-card-emoji">🍲</span>
        </div>
        <div className="dish-card-body">
          <h2 className="dish-card-title">{item.title}</h2>
          {description ? <p className="dish-card-description muted">{description}</p> : null}
          <p className="dish-card-meta muted">{publicCatalogCardMeta(item)}</p>
        </div>
      </Link>
    </article>
  );
}
