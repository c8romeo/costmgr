import type { ReactNode } from "react";

export default function FinopsBudgetPlanningLayout({
    children,
}: {
    children: ReactNode;
}) {
    return <section className="finops-budget-planning-layout">{children}</section>;
}
