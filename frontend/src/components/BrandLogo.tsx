type BrandLogoProps = {
  variant?: "compact" | "login";
  className?: string;
};

const SIZES = {
  compact: { width: 64, height: 64, className: "brand-logo-compact" },
  login: { width: 200, height: 200, className: "brand-logo-login" },
} as const;

export function BrandLogo({ variant = "compact", className }: BrandLogoProps) {
  const size = SIZES[variant];
  const classes = [size.className, className].filter(Boolean).join(" ");

  return (
    <picture className={classes}>
      <source srcSet="/logo-header.webp" type="image/webp" />
      <img
        src="/logo-header.png"
        alt=""
        width={size.width}
        height={size.height}
        decoding="async"
        className="brand-logo-image"
      />
    </picture>
  );
}
