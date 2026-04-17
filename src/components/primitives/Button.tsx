import type { ButtonHTMLAttributes, ReactNode } from "react";
import "./Button.scss";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md";
  children: ReactNode;
}

export function Button({
  variant = "secondary",
  size = "md",
  children,
  className = "",
  ...rest
}: Props) {
  return (
    <button
      {...rest}
      className={`btn btn-${variant} btn-${size} ${className}`.trim()}
    >
      {children}
    </button>
  );
}
