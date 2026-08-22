# 자주 묻는 질문 (FAQ)

**Version:** v1.0.0
**Last Updated:** 2026-08-22

---

## 1. ABC vs TDABC 차이는 무엇인가요?

- **ABC (Activity-Based Costing):** 활동을 기준으로 원가를 배분합니다. 간접비를 제품/서비스에 더 정확하게 배분할 수 있습니다.
- **TDABC (Time-Driven Activity-Based Costing):** 각 활동의 실제 소요 시간을 측정하여 원가를 배분합니다. ABC보다 데이터 수집이 간편하고, 미사용 용량을 분석할 수 있습니다.
- **costmgr는 두 가지를 결합**하여 사용합니다. ABC는 비용 동인 분석에, TDABC는 시간 기반 원가 추적에 사용됩니다.

## 2. 2FA 설정 방법은?

1. 우측 상단 프로필 → 보안 설정 클릭
2. TOTP 앱 (Google Authenticator, Authy, 1Password 등) 설치
3. "2FA 활성화" 클릭 → QR 코드 표시
4. 앱에서 QR 코드 스캔
5. 6자리 코드 입력 → 활성화 완료
6. 복구 코드 10개 안전하게 보관 (분실 시 계정 복구 불가)

## 3. 다중 테넌트 격리는 어떻게 작동하나요?

- PostgreSQL Row-Level Security (RLS)를 사용합니다.
- 각 요청은 tenant_id를 GUC (`app.tenant_id`)로 설정한 후 실행됩니다.
- 다른 tenant의 데이터는 RLS 정책에 의해 자동으로 차단됩니다.
- 자세한 내용은 [CR 0-2 lessons](../memory/cr-0-2-lessons.md) 참조.

## 4. AI 인사이트 정확도는?

- AI 인사이트는 참고용이며, 권위적이지 않습니다.
- confidence score가 낮은 항목은 사용자 확인을 요구합니다.
- 최종 의사결정 책임은 사용자에게 있습니다 (PRD §F10 + §UX v1.0 정합).

## 5. 백업 정책은?

- **PostgreSQL PITR (Point-in-Time Recovery):** 7일 자동 백업
- **PITR drill:** 분기별 1회 (RPO 4h / RTO 24h SLA)
- **Phase 4 wire (71a033a)** 정합 — 자세한 내용은 [docs/database-backup.md](./database-backup.md) 참조.

## 6. LISTEN/NOTIFY 실시간성은?

- PostgreSQL NOTIFY/LISTEN을 사용한 tenant fanout + multi-process coordination (Epic 13/14 wire 정합).
- 데이터 변경 → 모든 연결된 워커에 즉시 통지 → 캐시 무효화.
- 평균 지연: < 100ms (테넌트 단위)

## 7. 4-industry 지원 범위는?

- **manufacturing** (제조)
- **manufacturing_service** (제조 + 유통/서비스 겸영)
- **service** (서비스)
- **manufacturing_service_other** (제조 + 유통/서비스 + IT 겸영)

각 산업군별로 capability matrix가 다르게 적용됩니다 (CR 12-1 L4 precedent + capability-matrix.md 참조).

## 8. SSO enterprise 연동은?

- SAML 2.0 기반 (python3-saml==1.16.0)
- Epic 15 wire (5f9e37f) 정합
- JIT (Just-in-Time) user provisioning
- 다중 tenant IdP 메타데이터 라우팅

## 9. 결제 정책은?

- 월 1만원 (VAT 포함)
- 14일 무료 체험
- 매월 자동 결제 (해지 가능)

## 10. 환불 정책은?

- 14일 이내: 전액 환불
- 14일 초과: 일할 계산 환불
- 환불 처리: 최대 14 영업일

---

**이 FAQ는 costmgr 1st release (2026-08-22) 시점에 작성되었습니다.**
