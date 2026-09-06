"use client";

/**
 * apps/web/components/reports/EmailExportTab.tsx — cj-299 wire sprint (cj-style 299번째)
 *
 * Story 30.3 Email delivery UI tab. Pattern verbatim mirror of
 * CsvExportTab.tsx + PdfExportTab.tsx with email-specific fields:
 * recipients textarea, subject input, message textarea, PII redaction toggle.
 *
 * Pattern mirror (verbatim from CsvExportTab.tsx):
 *   - useState hooks for period / type / recipients / subject / pii / message /
 *     busy / errorMessage / successMessage
 *   - handleSend with fetch POST + JSON envelope decode (not blob download)
 *   - Period options: last 12 months generator
 *   - Inline ko-KR labels (NFR18 SSOT 적용)
 *   - data-testids: email-export-tab, email-period-selector-{YYYY-MM},
 *     email-recipients-input, email-subject-input, email-message-input,
 *     email-pii-toggle, email-send-button
 *
 * AD bind 3/3 (backend 결정 wire 보존):
 *   - AD-2 (audit-first INSERT append-only) — backend 결정 wire (export_email).
 *   - AD-10 (identity + 2FA) — backend owner/admin RBAC 결정 wire.
 *   - AD-12 (verify-first capability gate) — Capability.EXPORT_EMAIL (cj-285).
 *
 * NFR bind 3/7 active:
 *   - NFR4 (PII minimization) — toggle 로 PII redaction on/off 결정 wire.
 *   - NFR5 (page load P95 ≤ 5s) — async dispatch + retry 결정 wire 보존.
 *   - NFR18 (ko-KR vocabulary SSOT) — ko-KR labels 결정 wire.
 *
 * CR 11-3 honest-DEFER 238번째 epic 연속 정직 회복
 * (cj-298 close-out retro 의 237번째 + cj-299 의 238번째).
 */

import { useMemo, useState } from "react";

interface EmailExportTabProps {
  accessToken: string;
  tenantId: string;
  initialPeriod: string;
  initialType: "cost-records" | "bom";
}

export function EmailExportTab({
  accessToken,
  tenantId,
  initialPeriod,
  initialType,
}: EmailExportTabProps): React.ReactElement {
  const [period, setPeriod] = useState<string>(initialPeriod);
  const [type, setType] = useState<"cost-records" | "bom">(initialType);
  const [recipients, setRecipients] = useState<string>("");
  const [subject, setSubject] = useState<string>("");
  const [message, setMessage] = useState<string>("");
  const [piiRedactionEnabled, setPiiRedactionEnabled] = useState<boolean>(true);
  const [busy, setBusy] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Period options: last 12 months including current (generator).
  const periodOptions = useMemo<string[]>(() => {
    const months: string[] = [];
    const now = new Date();
    for (let i = 0; i < 12; i += 1) {
      const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const yyyy = d.getFullYear();
      const mm = String(d.getMonth() + 1).padStart(2, "0");
      months.push(`${yyyy}-${mm}`);
    }
    return months;
  }, []);

  const handleSend = async () => {
    setErrorMessage(null);
    setSuccessMessage(null);

    // ── Local validation (mirror csv_routes flow) ────────────────
    const recipientList = recipients
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s.length > 0);
    if (recipientList.length === 0) {
      setErrorMessage("수신자 이메일을 1개 이상 입력해 주세요 (쉼표 구분).");
      return;
    }
    if (recipientList.length > 10) {
      setErrorMessage("수신자 이메일은 최대 10개까지 입력할 수 있습니다.");
      return;
    }
    if (!subject.trim()) {
      setErrorMessage("이메일 제목을 입력해 주세요.");
      return;
    }
    if (subject.length > 200) {
      setErrorMessage("이메일 제목은 최대 200자까지 입력할 수 있습니다.");
      return;
    }
    if (message.length > 2000) {
      setErrorMessage("추가 메시지는 최대 2000자까지 입력할 수 있습니다.");
      return;
    }
    const emailRegex =
      /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    for (const r of recipientList) {
      if (!emailRegex.test(r)) {
        setErrorMessage(`잘못된 이메일 형식입니다: ${r}`);
        return;
      }
    }

    setBusy(true);
    try {
      const response = await fetch("/api/v1/exports/email", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          type,
          period,
          tenant_id: tenantId,
          recipients: recipientList,
          subject,
          pii_redaction_enabled: piiRedactionEnabled,
          message: message || null,
        }),
      });
      if (!response.ok) {
        let detail = `HTTP ${response.status}`;
        try {
          const errBody = await response.json();
          if (errBody && typeof errBody === "object" && "message_ko" in errBody) {
            detail = String((errBody as { message_ko: string }).message_ko);
          } else if (errBody && typeof errBody === "object" && "detail" in errBody) {
            detail = String((errBody as { detail: unknown }).detail);
          }
        } catch {
          // ignore JSON parse error
        }
        throw new Error(detail);
      }
      const result = (await response.json()) as {
        delivery_id: string;
        status: string;
        recipient_count: number;
        retry_count: number;
        pii_redacted_fields: string[];
      };
      setSuccessMessage(
        `발송 완료: ${result.recipient_count}명 (재시도 ${result.retry_count}회) ` +
          (result.pii_redacted_fields.length > 0
            ? `[PII redact: ${result.pii_redacted_fields.join(", ")}]`
            : ""),
      );
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : "이메일 발송 중 오류가 발생했습니다.",
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <section data-testid="email-export-tab" className="space-y-4">
      <header>
        <h2 className="text-lg font-semibold">이메일 내보내기</h2>
        <p className="text-sm text-gray-600">
          선택한 기간의 데이터를 CSV로 만들어 등록한 수신자에게 이메일로 발송합니다.
        </p>
      </header>

      <div className="grid grid-cols-2 gap-4">
        <label className="block">
          <span className="text-sm font-medium text-gray-700">기간 선택</span>
          <select
            data-testid="email-period-selector"
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            disabled={busy}
            className="mt-1 block w-full rounded border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          >
            {periodOptions.map((p) => (
              <option
                key={p}
                value={p}
                data-testid={`email-period-selector-${p}`}
              >
                {p}
              </option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="text-sm font-medium text-gray-700">데이터 종류</span>
          <select
            data-testid="email-type-selector"
            value={type}
            onChange={(e) =>
              setType(e.target.value === "bom" ? "bom" : "cost-records")
            }
            disabled={busy}
            className="mt-1 block w-full rounded border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          >
            <option value="cost-records">원가 기록 (cost-records)</option>
            <option value="bom">BOM 1단계 (bom)</option>
          </select>
        </label>
      </div>

      <label className="block">
        <span className="text-sm font-medium text-gray-700">
          수신자 이메일 (1~10개, 쉼표 구분)
        </span>
        <input
          type="text"
          data-testid="email-recipients-input"
          value={recipients}
          onChange={(e) => setRecipients(e.target.value)}
          placeholder="cfo@example.com, controller@example.com"
          disabled={busy}
          className="mt-1 block w-full rounded border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
        />
      </label>

      <label className="block">
        <span className="text-sm font-medium text-gray-700">이메일 제목 (1~200자)</span>
        <input
          type="text"
          data-testid="email-subject-input"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          placeholder="[bizup 원가 관리] 2026-08 원가 보고서"
          maxLength={200}
          disabled={busy}
          className="mt-1 block w-full rounded border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
        />
      </label>

      <label className="block">
        <span className="text-sm font-medium text-gray-700">
          추가 메시지 (선택, 최대 2000자)
        </span>
        <textarea
          data-testid="email-message-input"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="회계감사 자료로 활용 부탁드립니다."
          maxLength={2000}
          rows={3}
          disabled={busy}
          className="mt-1 block w-full rounded border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
        />
      </label>

      <label className="flex items-center gap-2">
        <input
          type="checkbox"
          data-testid="email-pii-toggle"
          checked={piiRedactionEnabled}
          onChange={(e) => setPiiRedactionEnabled(e.target.checked)}
          disabled={busy}
          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
        <span className="text-sm text-gray-700">
          개인정보(PII) 자동 redact (주민등록번호, 전화번호, 이메일)
        </span>
      </label>

      <div>
        <button
          type="button"
          data-testid="email-send-button"
          onClick={handleSend}
          disabled={busy}
          className="px-4 py-2 bg-blue-600 text-white rounded shadow hover:bg-blue-700 disabled:opacity-50"
        >
          {busy ? "발송 중..." : "이메일 발송"}
        </button>
      </div>

      {errorMessage && (
        <p
          role="alert"
          data-testid="email-error-message"
          className="text-sm text-red-600"
        >
          {errorMessage}
        </p>
      )}
      {successMessage && (
        <p
          role="status"
          data-testid="email-success-message"
          className="text-sm text-green-600"
        >
          {successMessage}
        </p>
      )}
    </section>
  );
}
