import type { ReactNode } from "react";

export default function FinopsUnitEconomicsLayout({
    children,
}: {
    children: ReactNode;
}) {
    return <section className="finops-unit-economics-layout">{children}</section>;
}
