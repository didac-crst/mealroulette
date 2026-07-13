import { useEffect, useId, useMemo, useRef, useState } from "react";

export type SearchSelectOption = {
  value: string;
  label: string;
};

export type SearchSelectProps = {
  value: string;
  options: SearchSelectOption[];
  onChange: (value: string) => void;
  placeholder?: string;
  emptyLabel?: string;
  disabled?: boolean;
  ariaLabel: string;
  className?: string;
};

export function SearchSelect({
  value,
  options,
  onChange,
  placeholder = "Search…",
  emptyLabel = "—",
  disabled = false,
  ariaLabel,
  className,
}: SearchSelectProps) {
  const listId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");

  const selectedLabel = options.find((option) => option.value === value)?.label ?? "";
  const displayValue = open ? query : selectedLabel;

  const filteredOptions = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) {
      return options;
    }
    return options.filter((option) => option.label.toLowerCase().includes(normalized));
  }, [options, query]);

  useEffect(() => {
    if (!open) {
      return;
    }
    function handlePointerDown(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
        setQuery("");
      }
    }
    document.addEventListener("mousedown", handlePointerDown);
    return () => document.removeEventListener("mousedown", handlePointerDown);
  }, [open]);

  function selectOption(nextValue: string) {
    onChange(nextValue);
    setOpen(false);
    setQuery("");
  }

  return (
    <div
      ref={rootRef}
      className={["search-select", open ? "search-select-open" : "", className].filter(Boolean).join(" ")}
    >
      <label className="search-select-label">
        <span className="visually-hidden">{ariaLabel}</span>
        <input
          type="search"
          className="search-select-input"
          value={displayValue}
          placeholder={value ? selectedLabel : placeholder}
          disabled={disabled}
          aria-label={ariaLabel}
          aria-expanded={open}
          aria-controls={listId}
          aria-autocomplete="list"
          role="combobox"
          onFocus={() => {
            if (!disabled) {
              setOpen(true);
              setQuery(selectedLabel);
            }
          }}
          onChange={(event) => {
            setQuery(event.target.value);
            setOpen(true);
          }}
          onKeyDown={(event) => {
            if (event.key === "Escape") {
              setOpen(false);
              setQuery("");
            }
          }}
        />
      </label>
      {open && !disabled ? (
        <ul id={listId} className="search-select-list" role="listbox">
          <li>
            <button type="button" className="search-select-option" role="option" onClick={() => selectOption("")}>
              {emptyLabel}
            </button>
          </li>
          {filteredOptions.length === 0 ? (
            <li className="search-select-empty muted">No matches</li>
          ) : (
            filteredOptions.map((option) => (
              <li key={option.value}>
                <button
                  type="button"
                  className={`search-select-option${option.value === value ? " search-select-option-active" : ""}`}
                  role="option"
                  aria-selected={option.value === value}
                  onClick={() => selectOption(option.value)}
                >
                  {option.label}
                </button>
              </li>
            ))
          )}
        </ul>
      ) : null}
    </div>
  );
}
