import { cn } from "@/lib/utils";

type StatusVariant = "success" | "warning" | "danger" | "neutral";

const VARIANT_CLASSES: Record<StatusVariant, string> = {
  success: "bg-success/15 text-success border-success/25",
  warning: "bg-warning/15 text-warning-foreground border-warning/25",
  danger: "bg-danger/15 text-danger border-danger/25",
  neutral: "bg-muted text-muted-foreground border-border",
};

interface StatusBadgeProps {
  variant: StatusVariant;
  children: React.ReactNode;
  className?: string;
  dot?: boolean;
}

export function StatusBadge({
  variant,
  children,
  className,
  dot = false,
}: StatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        VARIANT_CLASSES[variant],
        className
      )}
    >
      {dot && (
        <span
          className={cn(
            "size-1.5 rounded-full",
            variant === "success" && "bg-success",
            variant === "warning" && "bg-warning",
            variant === "danger" && "bg-danger",
            variant === "neutral" && "bg-muted-foreground"
          )}
        />
      )}
      {children}
    </span>
  );
}

export function getRunStatusVariant(
  status: string
): StatusVariant {
  switch (status) {
    case "completed":
      return "success";
    case "running":
      return "warning";
    case "failed":
      return "danger";
    case "partial":
      return "warning";
    default:
      return "neutral";
  }
}

export function getConfidenceVariant(confidence: number): StatusVariant {
  if (confidence >= 0.8) return "success";
  if (confidence >= 0.5) return "warning";
  return "danger";
}

export function getImpactVariant(score: number): StatusVariant {
  if (score >= 7) return "success";
  if (score >= 4) return "warning";
  return "danger";
}
