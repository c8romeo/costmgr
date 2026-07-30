/**
 * apps/web/components/settings/wizard/WizardErrorBoundary.tsx
 *
 * Story 1.2 — Task 9.1 (F-24). Client-side React error boundary for the
 * settings wizard. Catches render-phase exceptions thrown by any of the
 * 4 step components (or by `useSettingsCompletion` during polling) and
 * renders a recoverable fallback instead of unmounting the page to a
 * blank screen.
 *
 * Why a class component: React's `componentDidCatch` API only exists on
 * class components. Server Components cannot host an error boundary —
 * it must be a Client Component child of the RSC tree.
 *
 * UX-locked (Story ux-locked-decisions §4): ko-KR copy, Professional
 * 톤, WCAG AA contrast.
 */

"use client";

import { Component, type ReactNode } from "react";

export interface WizardErrorBoundaryProps {
  children: ReactNode;
}

export interface WizardErrorBoundaryState {
  error: Error | null;
}

export class WizardErrorBoundary extends Component<
  WizardErrorBoundaryProps,
  WizardErrorBoundaryState
> {
  override state: WizardErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): WizardErrorBoundaryState {
    return { error };
  }

  override componentDidCatch(error: Error, info: { componentStack: string }) {
    // The hook already surfaces parse/network failures via its own state
    // (F-30: clears cached status on error). This boundary is the last
    // line of defence — log it so we can spot render-phase regressions.
    // eslint-disable-next-line no-console
    console.error("[wizard-error-boundary]", error, info.componentStack);
  }

  reset = () => {
    this.setState({ error: null });
  };

  override render() {
    if (this.state.error) {
      return (
        <section
          role="alert"
          aria-live="assertive"
          style={{
            padding: "1rem 1.25rem",
            border: "1px solid #fca5a5",
            background: "#fee2e2",
            color: "#991b1b",
            borderRadius: 8,
            marginBottom: "1rem",
          }}
        >
          <h2
            style={{
              fontSize: "1.05rem",
              fontWeight: 700,
              marginBottom: 6,
            }}
          >
            ⚠️ 마법사를 표시하는 중 문제가 발생했습니다
          </h2>
          <p style={{ marginBottom: "0.75rem", fontSize: "0.9rem" }}>
            잠시 후 다시 시도해 주세요. 문제가 계속되면 관리자에게
            아래 메시지를 전달해 주세요.
          </p>
          <pre
            style={{
              padding: "0.5rem 0.75rem",
              background: "rgba(0,0,0,0.05)",
              borderRadius: 4,
              fontSize: "0.8rem",
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
              marginBottom: "0.75rem",
            }}
          >
            {this.state.error.message}
          </pre>
          <button
            type="button"
            onClick={this.reset}
            style={{
              padding: "0.4rem 0.85rem",
              background: "#991b1b",
              color: "#fef2f2",
              border: "none",
              borderRadius: 6,
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            다시 시도
          </button>
        </section>
      );
    }
    return this.props.children;
  }
}