import type { KeyboardEvent } from "react";

type Props = {
  value: number | null;
  disabled?: boolean;
  onChange: (value: number) => void;
};

export function StarRating({ value, disabled = false, onChange }: Props) {
  function handleKeyDown(event: KeyboardEvent<HTMLButtonElement>, star: number) {
    if (disabled) {
      return;
    }
    if (event.key === "ArrowRight" || event.key === "ArrowUp") {
      event.preventDefault();
      onChange(value === null ? 1 : Math.min(5, value + 1));
    } else if (event.key === "ArrowLeft" || event.key === "ArrowDown") {
      event.preventDefault();
      onChange(value === null ? 1 : Math.max(1, value - 1));
    } else if (event.key === " " || event.key === "Enter") {
      event.preventDefault();
      onChange(star);
    }
  }

  return (
    <div className="star-rating" role="radiogroup" aria-label="Rating">
      {[1, 2, 3, 4, 5].map((star) => {
        const filled = value !== null && star <= value;
        return (
          <button
            key={star}
            type="button"
            className={`star-rating-star${filled ? " star-rating-star-filled" : ""}`}
            disabled={disabled}
            role="radio"
            aria-checked={value === star}
            aria-label={`${star} star${star === 1 ? "" : "s"}`}
            onClick={() => onChange(star)}
            onKeyDown={(event) => handleKeyDown(event, star)}
          >
            ★
          </button>
        );
      })}
    </div>
  );
}
