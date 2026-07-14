type BrandLogoProps = {
  variant?: "compact" | "login";
  className?: string;
};

const SIZES = {
  compact: { width: 40, height: 40, className: "brand-logo-compact" },
  login: { width: 160, height: 160, className: "brand-logo-login" },
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
        className="brand-logo-image"
      />
    </picture>
  );
}
