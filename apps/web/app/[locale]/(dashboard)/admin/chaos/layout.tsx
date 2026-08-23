/**
 * apps/web/app/[locale]/(dashboard)/admin/chaos/layout.tsx —
 * Phase 9 (cj-style 99번째 wire) — Layout wrapper for the chaos admin
 * dashboard section. Preserves the parent layout's auth/menu surface
 * and ensures RTL test wrapper inheritance (CR 11-4 D-002 verbatim).
 */
export default function ChaosAdminLayout({
  children,
}: {
  children: React.ReactNode;
}): React.ReactElement {
  return <section data-section="chaos-admin-dashboard">{children}</section>;
}
