"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { activeDestination, NAVIGATION } from "@/lib/navigation";

export default function AppNavigation() {
  const pathname = usePathname();
  const active = activeDestination(pathname);
  if (!active) return null;
  const links = NAVIGATION.map((item) => <Link key={item.href} href={item.href} aria-current={active === item.href ? "page" : undefined} className="shrink-0 rounded-lg px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-indigo-600 aria-[current=page]:bg-indigo-50 aria-[current=page]:text-indigo-800">{item.label}</Link>);
  return <div className="border-b border-slate-200 bg-white">
    <nav aria-label="CareerPilot main navigation" className="mx-auto hidden max-w-7xl flex-wrap gap-1 px-5 py-3 lg:flex">{links}</nav>
    <details key={pathname} className="mx-auto max-w-7xl px-5 py-3 lg:hidden"><summary className="cursor-pointer rounded-lg py-2 text-sm font-semibold text-slate-800">Navigate CareerPilot · {NAVIGATION.find((item) => item.href === active)?.label}</summary><nav aria-label="CareerPilot mobile navigation" className="mt-2 grid gap-1 sm:grid-cols-2">{links}</nav></details>
  </div>;
}
