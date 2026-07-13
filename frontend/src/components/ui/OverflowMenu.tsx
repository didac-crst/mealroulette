import { useEffect, useId, useRef, useState, type ReactNode } from "react";

export type OverflowMenuItem = {
  id: string;
  label: ReactNode;
  onClick: () => void;
  disabled?: boolean;
  variant?: "default" | "danger";
};

export type OverflowMenuProps = {
  items: OverflowMenuItem[];
  ariaLabel?: string;
  className?: string;
};

export function OverflowMenu({ items, ariaLabel = "More actions", className }: OverflowMenuProps) {
  const menuId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
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
    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [open]);

  if (items.length === 0) {
    return null;
  }

  return (
    <div ref={rootRef} className={["overflow-menu", className].filter(Boolean).join(" ")}>
      <button
        type="button"
        className="button button-ghost button-sm overflow-menu-trigger"
        aria-label={ariaLabel}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={menuId}
        onClick={() => setOpen((current) => !current)}
      >
        More
      </button>
      {open ? (
        <div id={menuId} className="overflow-menu-panel" role="menu">
          {items.map((item) => (
            <button
              key={item.id}
              type="button"
              role="menuitem"
              className={[
                "overflow-menu-item",
                item.variant === "danger" ? "overflow-menu-item-danger" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              disabled={item.disabled}
              onClick={() => {
                setOpen(false);
                item.onClick();
              }}
            >
              {item.label}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
