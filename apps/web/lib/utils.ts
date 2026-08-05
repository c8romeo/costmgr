// apps/web/lib/utils.ts — shadcn-style cn helper
// Story 0.5 — T2.4 (AC #2)
//
// `cn` composes className values via clsx (conditional joining) then
// resolves Tailwind class conflicts via tailwind-merge. This is the
// shadcn/ui convention for className composition.

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
