/**
 * apps/web/components/dashboard/KpiCard.tsx — 단일 KPI 타일.
 *
 * cj-style N+19 (2026-09-15 KST, D-Day+1, Dashboard 보강 A=KPI+빠른진입).
 * 결정 wire 보존: 4개 KPI 카드 (매출/원가/마진/마진율) 의 단일 카드 컴포넌트.
 * UX-locked: WCAG AA contrast (Story ux-locked-decisions), ko-KR 라벨,
 * 슬레이트 톤 (#475569 secondary text, 값 color 는 의미 기반 강조).
 */

export interface KpiCardProps {
  label: string;
  /** 표시할 값 — 문자열로 직접 받음 (format은 호출자가 결정). */
  value: string;
  /** 값 텍스트 색상 (의미: 매출=teal, 원가=red, 마진=blue/red, 마진율=violet). */
  color: string;
}

export function KpiCard({ label, value, color }: KpiCardProps) {
  return (
    <div
      style={{
        padding: "16px 18px",
        background: "#ffffff",
        border: "1px solid #e2e8f0",
        borderRadius: 8,
        boxShadow: "0 1px 2px rgba(15, 23, 42, 0.04)",
      }}
    >
      <div style={{ fontSize: "0.85rem", color: "#475569", marginBottom: 8 }}>{label}</div>
      <div
        style={{
          fontSize: "1.4rem",
          fontWeight: 700,
          color,
          fontVariantNumeric: "tabular-nums",
          letterSpacing: "-0.01em",
        }}
      >
        {value}
      </div>
    </div>
  );
}
