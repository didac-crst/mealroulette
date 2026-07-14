import { useEffect, useId, useRef, useState } from "react";
import { Link } from "react-router-dom";

import type { CookOption } from "./todayMeals";

type Props = {
  options: CookOption[];
  loading?: boolean;
};

export function CookMealMenu({ options, loading = false }: Props) {
  const menuId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) {
      return;
    }

    function handlePointerDown(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
        triggerRef.current?.focus();
      }
    }

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  if (loading) {
    return (
      <button type="button" className="button" disabled>
        Cook
      </button>
    );
  }

  if (options.length === 0) {
    return <span className="muted">No recipe to cook</span>;
  }

  if (options.length === 1) {
    const option = options[0];
    return (
      <Link to={`/recipes/${option.recipeId}/cook`} className="button">
        Cook
      </Link>
    );
  }

  return (
    <div ref={rootRef} className="overflow-menu cook-meal-menu">
      <button
        ref={triggerRef}
        type="button"
        className="button cook-meal-menu-trigger"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={menuId}
        onClick={() => setOpen((current) => !current)}
      >
        Cook
      </button>
      {open ? (
        <div id={menuId} ref={menuRef} className="overflow-menu-panel" role="menu">
          {options.map((option) => (
            <Link
              key={option.key}
              to={`/recipes/${option.recipeId}/cook`}
              role="menuitem"
              className="overflow-menu-item"
              onClick={() => setOpen(false)}
            >
              {option.dishName}
              <span className="muted"> · {option.roleLabel}</span>
            </Link>
          ))}
        </div>
      ) : null}
    </div>
  );
}
