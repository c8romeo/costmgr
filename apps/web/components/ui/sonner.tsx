// apps/web/components/ui/sonner.tsx — shadcn/ui sonner Toaster wrapper
// Story 0.5 — T3.2 (AC #3)
//
// Wraps sonner's Toaster with shadcn-style defaults:
//   - theme="light" (dark mode auto-switch deferred to theme story)
//   - richColors=true (semantic colors per toast variant)
//   - position="top-right" (shadcn convention)
//   - closeButton enabled

"use client";

import { Toaster as SonnerToaster } from "sonner";

type ToasterProps = React.ComponentProps<typeof SonnerToaster>;

export function Toaster(props: ToasterProps) {
  return (
    <SonnerToaster
      theme="light"
      richColors
      position="top-right"
      closeButton
      {...props}
    />
  );
}
