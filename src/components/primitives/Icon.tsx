import type { LucideIcon, LucideProps } from "lucide-react";

interface Props extends LucideProps {
  icon: LucideIcon;
}

export function Icon({ icon: IconComponent, size = 16, strokeWidth = 1.75, ...rest }: Props) {
  return <IconComponent aria-hidden size={size} strokeWidth={strokeWidth} {...rest} />;
}
