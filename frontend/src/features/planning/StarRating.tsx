type Props = {
  value: number | null;
  disabled?: boolean;
  onChange: (value: number) => void;
};

export function StarRating({ value, disabled = false, onChange }: Props) {
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
          >
            ★
          </button>
        );
      })}
    </div>
  );
}
