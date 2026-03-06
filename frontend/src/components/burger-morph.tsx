"use client";

import { cn } from "@/lib/utils";

interface BurgerMorphProps {
  open: boolean;
  className?: string;
}

export function BurgerMorph({ open, className }: BurgerMorphProps) {
  return (
    <div className={cn("relative size-5", className)}>
      {/* Top line -> rotates to form \ of X */}
      <span
        className={cn(
          "absolute left-0 block h-[2px] w-5 rounded-full bg-current transition-all duration-300 ease-in-out",
          open ? "top-[9px] rotate-45" : "top-[3px] rotate-0"
        )}
      />
      {/* Middle line -> fades out */}
      <span
        className={cn(
          "absolute left-0 top-[9px] block h-[2px] w-5 rounded-full bg-current transition-all duration-200 ease-in-out",
          open ? "scale-x-0 opacity-0" : "scale-x-100 opacity-100"
        )}
      />
      {/* Bottom line -> rotates to form / of X */}
      <span
        className={cn(
          "absolute left-0 block h-[2px] w-5 rounded-full bg-current transition-all duration-300 ease-in-out",
          open ? "top-[9px] -rotate-45" : "top-[15px] rotate-0"
        )}
      />
    </div>
  );
}
