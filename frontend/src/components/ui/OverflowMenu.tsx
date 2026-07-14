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
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const wasOpenRef = useRef(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) {
      return;
    }

    const menu = menuRef.current;
    const menuItems = menu ? Array.from(menu.querySelectorAll<HTMLButtonElement>('[role="menuitem"]')) : [];
    const enabledItems = menuItems.filter((item) => !item.disabled);
    enabledItems[0]?.focus();

    function handlePointerDown(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
        triggerRef.current?.focus();
        return;
      }

      if (!menu || enabledItems.length === 0) {
        return;
      }

      const activeIndex = enabledItems.findIndex((item) => item === document.activeElement);
      if (event.key === "ArrowDown") {
        event.preventDefault();
        const next = activeIndex < 0 ? 0 : (activeIndex + 1) % enabledItems.length;
        enabledItems[next]?.focus();
        return;
      }
      if (event.key === "ArrowUp") {
        event.preventDefault();
        const next =
          activeIndex < 0
            ? enabledItems.length - 1
            : (activeIndex - 1 + enabledItems.length) % enabledItems.length;
        enabledItems[next]?.focus();
      }
    }

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open, items]);

  useEffect(() => {
    if (wasOpenRef.current && !open) {
      triggerRef.current?.focus();
    }
    wasOpenRef.current = open;
  }, [open]);

  if (items.length === 0) {
    return null;
  }

  return (
    <div ref={rootRef} className={["overflow-menu", className].filter(Boolean).join(" ")}>
      <button
        ref={triggerRef}
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
        <div id={menuId} ref={menuRef} className="overflow-menu-panel" role="menu">
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
