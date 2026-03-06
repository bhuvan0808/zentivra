"use client";

import { useSidebar } from "./sidebar-context";
import { BurgerMorph } from "./burger-morph";

interface PageHeaderProps {
  title: string;
  description?: string;
  children?: React.ReactNode;
}

export function PageHeader({ title, description, children }: PageHeaderProps) {
  const { open, toggle } = useSidebar();

  return (
    <div className="mb-6">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          {/* Mobile burger */}
          <button
            onClick={toggle}
            className="flex items-center justify-center lg:hidden"
            aria-label="Open menu"
          >
            <BurgerMorph open={open} />
          </button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight lg:text-3xl">
              {title}
            </h1>
            {description && (
              <p className="mt-1 text-sm text-muted-foreground">
                {description}
              </p>
            )}
          </div>
        </div>
        {children && (
          <div className="flex w-full flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center md:w-auto md:shrink-0 md:justify-end">
            {children}
          </div>
        )}
      </div>
    </div>
  );
}
