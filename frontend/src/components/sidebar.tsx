"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Globe,
  Play,
  Search,
  FileText,
  Radar,
  LogOut,
  Bot,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Separator } from "@/components/ui/separator";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useSidebar } from "./sidebar-context";
import { BurgerMorph } from "./burger-morph";
import { getMe, logout } from "@/lib/api";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/sources", label: "Sources", icon: Globe },
  { href: "/runs", label: "Runs", icon: Play },
  { href: "/findings", label: "Findings", icon: Search },
  { href: "/digests", label: "Digests", icon: FileText },
  { href: "/agents", label: "Agents", icon: Bot },
  { href: "/oops", label: "Oops", icon: Sparkles },
] as const;

function getInitials(name: string): string {
  const words = name.trim().split(/\s+/);
  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase();
  }
  return name.slice(0, 2).toUpperCase();
}

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { open, toggle, close } = useSidebar();

  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");

  useEffect(() => {
    getMe().then((res) => {
      if (res.ok) {
        setDisplayName(res.data.display_name);
        setEmail(res.data.email ?? "");
      }
    });
  }, []);

  const initials = displayName ? getInitials(displayName) : "??";

  const isActive = (href: string) => pathname.startsWith(href);

  async function handleLogout() {
    await logout();
    localStorage.removeItem("auth_token");
    localStorage.removeItem("user_email");
    router.push("/signin");
  }

  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/40 lg:hidden"
          onClick={close}
        />
      )}

      {/* Sidebar panel */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-60 flex-col border-r border-sidebar-border bg-sidebar transition-transform duration-200 lg:static lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex h-14 items-center gap-3 px-4">
          {/* Close morph button on mobile */}
          <button
            onClick={toggle}
            className="flex items-center justify-center lg:hidden"
            aria-label="Close menu"
          >
            <BurgerMorph open={open} />
          </button>
          <div className="hidden lg:flex items-center gap-2">
            <Radar className="size-6 text-sidebar-foreground" />
          </div>
          <span className="text-lg font-bold tracking-tight">Zentivra</span>

          {/* Avatar dropdown — pushed to the right */}
          <div className="ml-auto">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button
                  className="flex size-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-semibold cursor-pointer transition-transform hover:scale-105 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  aria-label="User menu"
                >
                  {initials}
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-52">
                <DropdownMenuLabel className="font-normal">
                  <p className="text-sm font-medium leading-none">
                    {displayName || "User"}
                  </p>
                  {email && (
                    <p className="mt-1 text-xs text-muted-foreground truncate">
                      {email}
                    </p>
                  )}
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={handleLogout}
                  className="cursor-pointer text-destructive focus:text-destructive"
                >
                  <LogOut className="mr-2 size-4" />
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
        <Separator className="bg-sidebar-border" />
        <nav className="mt-4 flex flex-1 flex-col gap-1 overflow-y-auto px-3">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              onClick={close}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive(href)
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground",
              )}
            >
              <Icon className="size-4 shrink-0" />
              {label}
            </Link>
          ))}
        </nav>
        <div className="px-5 py-4">
          <p className="text-xs text-sidebar-foreground/40">
            Frontier AI Radar v1.0
          </p>
        </div>
      </aside>
    </>
  );
}
