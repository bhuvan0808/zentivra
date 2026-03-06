"use client";

import { motion } from "framer-motion";
import { TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";

interface AnimatedRowProps {
  index: number;
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

const MotionTableRow = motion.create(TableRow);

export function AnimatedRow({ index, children, className, onClick }: AnimatedRowProps) {
  return (
    <MotionTableRow
      initial={{ opacity: 0, filter: "blur(4px)" }}
      animate={{ opacity: 1, filter: "blur(0px)" }}
      transition={{
        duration: 0.35,
        delay: index * 0.05,
        ease: "easeOut",
      }}
      className={cn(className)}
      onClick={onClick}
    >
      {children}
    </MotionTableRow>
  );
}
