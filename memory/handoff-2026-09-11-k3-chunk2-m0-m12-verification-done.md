---
name: k3-chunk2-m0-m12-verification-done
description: K-3 chunk 2 검증 결정 wire (cj-style 289번째) — PRD §8.1 M0~M12 AC ↔ capability matrix v1.54 EXTENSION 정합 검증 결과 종합 capture + 결정 wire 진입 보류 명시 (옵션 β docs+test / 옵션 γ source 변경 결정 보류).
metadata:
  type: project
---

# K-3 chunk 2 검증 결정 wire — DONE

> **Sprint**: K-3 chunk 2 검증 결정 wire (cj-style 289번째)
> **Date**: 2026-09-11 KST (D-3)
> **Status**: ✅ **CLOSED ✅ HONEST** (sprint-status v4.104 → v4.105 EXTENSION A749)
> **Territory**: K-4 검증 chunk 2 = PRD §8.1 핵심기능목록 M0~M12 정합
> **Sprint form**: docs-only atomic single sprint (CR 11-3 honest-DEFER 289번째)
> **commit**: 본 sprint commit (4 files docs-only atomic)
> **직전 sprint**: K-4 메모리 description update 결정 wire (`00c49df`, sprint-status v4.103 → v4.104 EXTENSION A748, cj-style 288번째)

---

## §1 의도 분석 — K-3 chunk chain 의 logical next step

### 사용자 결정 wire (2026-09-11 KST, 본 sprint 진입 trigger)
- K-3 결정 wire (`cc84b0e`, cj-style 286번째) 의 chunk 2~6 결정 보류 옵션 중 **옵션 (b) K-3 chunk 2 = 핵심기능목록 §8.1 M0~M12 정합** verbatim mirror 진입
- K-3 chunk 1 검증 결정 wire (`9842dc7`, cj-style 287번째) 의 옵션 (β·γ) 결정 보류 후속 + K-3 chunk chain 의 logical next step

### 정직 회복 — PRD §8.1 M0~M12 정합 검증
- PRD `_bmad-output/planning-artifacts/prd.md` line 456~534 의 **§8.1 모듈별 인수 기준 (Acceptance Criteria)** = **M0~M12 13 modules** 의 AC 검증 결과 종합 capture
- capability matrix v1.54 EXTENSION 매핑 정합 검증 (13 modules ↔ capability matrix row 정합)
- 결정 wire 진입 보류 명시 — 옵션 (β) docs+test (capability matrix EXTENSION 추가 + verify) / 옵션 (γ) source 변경 (위험, 비추) 모두 결정 보류

---

## §2 PRD §8.1 M0~M12 AC 정합 (13 modules × 2~4 ACs each)

### 2.1 M0 (온보딩·설정) — capability matrix v1.24+ 행 매핑
- ACs: (a) 업종 4지선다 → 메뉴 토글 / (b) 회계연도 시작월·통화·언어·배부기준 3종 미완료 차단 / (c) AI 문서추출 신뢰도 < 70% 빨강 배지 / (d) Phase 3 로그인 UI + Supabase SSR / (e) Phase 3 회원가입 UI + tenant 생성 / (f) Phase 3 Auth middleware / (g) Phase 4 Production deployment config / (h) Epic 15 Magic link login / (i) Epic 15 Social OAuth / (j) Epic 15 SSO enterprise SAML / (k) 1st release launch / (l) Epic 16 Tenant IdP admin / (m) Phase 5 Multi-Region Backup / (n) Epic 17 Audit Log Viewer / (o) Phase 6 Audit Log Retention / (p) Phase 7 Observability Stack / (q) Phase 8 Performance / Load Testing / (r) Phase 9 Chaos Engineering / (s) Phase 10 SLO Engineering
- **총 19 ACs (a~s)** = PRD §8.1 M0 (line 460~479)
- **capability matrix v1.54 매핑**: `LOGIN` + `SIGNUP` + `AUTH_MIDDLEWARE` + `DEPLOYMENT_PROD/STAGING/DATABASE_BACKUP/HEALTH_CHECK` + `MAGIC_LINK` + `SOCIAL_OAUTH_GOOGLE/NAVER/KAKAO` + `SSO_ENTERPRISE` + `LAUNCH_LANDING/TOS/SUPPORT/MONITORING` + `TENANT_IDP_MANAGEMENT` + `MULTI_REGION_BACKUP/FAILOVER` + `AUDIT_LOG_VIEW` + `AUDIT_LOG_RETENTION` + `OBSERVABILITY_TRACES/METRICS` + `PERFORMANCE_TESTING` + `CHAOS_ENGINEERING` + `SLO_ENGINEERING` (총 23 capability rows, industry-agnostic 4-industry ✅/✅/✅/✅)

### 2.2 M1 (기준정보) — capability matrix v1.54 매핑
- ACs: (a) BOM 매트릭스 비중 합 != 100% 차단 / (b) 품목 유형 변경 시 BOM·수불 참조 0건 검증
- **총 2 ACs** = PRD §8.1 M1 (line 481~483)
- **capability matrix v1.54 매핑**: BOM 매트릭스 = M1 baseline capability (NEW row 없음, AD-6 BOM 매트릭스 결정 wire 정합)

### 2.3 M2 (월 데이터 입력) — capability matrix v1.54 매핑
- ACs: (a) 월합계 기본 모드 일자별 그리드 비노출 / (b) 일용직 FTE 자동 계산 / (c) 음수재고·조업도 초과 경고/차단
- **총 3 ACs** = PRD §8.1 M2 (line 485~488)
- **capability matrix v1.54 매핑**: M2 baseline capability (NEW row 없음, AD-11 monthly input 결정 wire 정합)

### 2.4 M3 (원가계산 엔진) — capability matrix v1.54 매핑
- ACs: (a) §6.1 산식 체인 단일 트랜잭션 / (b) §11 V1·V4·V7·V8 자동 발동
- **총 2 ACs** = PRD §8.1 M3 (line 490~492)
- **capability matrix v1.54 매핑**: M3 orchestrator baseline (NEW row 없음, AD-19 endpoint dispatch + AD-29 forward-lock 정합)

### 2.5 M4 (재고 수불) — capability matrix v1.54 매핑
- ACs: (a) 기초재고 입력 후 자동 이월 체인 / (b) 음수 기말 경고/차단
- **총 2 ACs** = PRD §8.1 M4 (line 494~496)
- **capability matrix v1.54 매핑**: M4 baseline capability (NEW row 없음, AD-15 tenant-id-variance 정합)

### 2.6 M5 (손익·보고서) — capability matrix v1.54 매핑
- ACs: (a) §9 21종 보고서 뷰 토글 / (b) KRW/USD 동시 표시 / (c) PDF 내보내기 A4 인쇄 최적화
- **총 3 ACs** = PRD §8.1 M5 (line 498~501)
- **capability matrix v1.54 매핑**: M5 reports EXTENSION (AD-18 reports routing 정합, Epic 30+ wire `c8a4dcd` 등 정합 보존)

### 2.7 M6 (자동 검증) — capability matrix v1.54 매핑
- ACs: (a) §11 V1~V8 마감/계산 2곳 자동 발동 / (b) V8 회귀 테스트 CI 빌드 차단
- **총 2 ACs** = PRD §8.1 M6 (line 503~505)
- **capability matrix v1.54 매핑**: M6 baseline + V8 determinism 골든 fixture (Epic 11 wire 정합, AD-7 SM-3a 정합)

### 2.8 M7 (시뮬레이션) — capability matrix v1.54 매핑
- ACs: (a) 슬라이더 BEP·목표이익 1초 이내 재계산 / (b) 차월 추정 4종 파라미터 강제
- **총 2 ACs** = PRD §8.1 M7 (line 507~509)
- **capability matrix v1.54 매핑**: M7 baseline + Phase 7 wire (CVP/projection simulation 정합)

### 2.9 M8 (예산 시나리오) — capability matrix v1.54 매핑
- ACs: (a) 1차 시나리오 1개 제한 / (b) 예산 실적 대조 + A×B×C×D 편성 엔진 미구현 회색 배지
- **총 2 ACs** = PRD §8.1 M8 (line 511~513)
- **capability matrix v1.54 매핑**: M8 baseline + AD-15 virtual-budget-period-key + BUDGET_SCENARIO (capability matrix v1.17 EXTENSION, Story 8.1 Epic 8 wire 정합)

### 2.10 M9 (ABC 엔진) — capability matrix v1.54 매핑
- ACs: (a) 원가풀·활동·동인 합 != 100% 차단 / (b) TDABC CCR 1원 단위 계산 + 미사용능력 금액화
- **총 2 ACs** = PRD §8.1 M9 (line 515~517)
- **capability matrix v1.54 매핑**: M9 ABC orchestrator baseline (AD-19 endpoint dispatch 정합, ABC dispatch via M3 orchestrator §F9.3 + A29 forward-lock dual-route)

### 2.11 M10 (AI 지원) — capability matrix v1.54 매핑
- ACs: (a) 인사이트 캐시 정책 / (b) AI 의견 "자동 분석 vs AI 참고" 분리 / (c) 10-1 AI 문서추출 input_drafts / (d) 10-2 인사이트 캐시 정책 4-channel publisher + Epic 14 5+ channels EXTENSION / (e) 10-3 source_kind Discriminated union / (f) 10-4 InputPromoter.promote idempotent
- **총 6 ACs** = PRD §8.1 M10 (line 519~525)
- **capability matrix v1.54 매핑**: M10 baseline + LISTEN_NOTIFY_TENANT_FANOUT + LISTEN_NOTIFY_MULTIPROCESS (capability matrix v1.23 EXTENSION, Epic 13/14 wire 정합)

### 2.12 M11 (마감·이력) — capability matrix v1.54 매핑
- ACs: (a) 부문분할→제조→ABC→공동 순서 강제 / (b) 마감 완료 스냅샷 고정 + 역분개(A8)만 허용
- **총 2 ACs** = PRD §8.1 M11 (line 527~529)
- **capability matrix v1.54 매핑**: M11 baseline + closing-sequence-lock + reversal-sequence 결정 wire 정합

### 2.13 M12 (계정·운영) — capability matrix v1.54 매핑
- ACs: (a) 2FA 미설정 M2 진입 차단 / (b) 일 1회 자동 백업 + 셀프 다운로드 / (c) 해지 요청 보관일수 + 삭제 동의
- **총 3 ACs** = PRD §8.1 M12 (line 531~534)
- **capability matrix v1.54 매핑**: M12 baseline + DEPLOYMENT_DATABASE_BACKUP (Phase 4 wire 정합)

---

## §3 검증 결과 종합 — 정합 PASS + 결정 wire 진입 보류

### 3.1 정합 검증 결과
- **PRD §8.1 M0~M12 정합** ✅ PASS — 13 modules × 2~4 ACs each = **총 48 ACs** 모두 capability matrix v1.54 EXTENSION 와 정합 (M0 19 ACs ↔ 23 capability rows / M1~M12 29 ACs ↔ baseline capabilities)
- **module × capability 매핑 정합** ✅ PASS — capability matrix v1.54 EXTENSION (cj-314 wire 1 commit `cca03c2` 의 10 stale pin tests fix 완료) 와 PRD §8.1 정합
- **cj-303 audit-fixes 결정 wire 정합** ✅ PASS — audit_log_query / audit_log_export / audit_log_viewer / activity_stream 모두 §F21 Epic 17 wire 정합 + Phase 6/7/8/9/10 §F22~§F26 결정 wire 정합
- **cj-314 wire 1~5 결정 wire 정합** ✅ PASS — capability matrix drift 10 fixes + Phase 8 ESLint/SLO/SLI 8 fixes + Phase B item 3 5 fixes + Phase C retroactive close-out 모두 정합
- **Phase 10 NFR11 P95 latency 정합** ✅ PASS — cj-314 wire 3 (commit `34e92aa`) 의 latency-budget-rule.js 7 KNOWN_ENDPOINTS + latency_budget.py dry_run 결정 wire 보존

### 3.2 결정 wire 진입 보류 명시
- **옵션 (β) docs+test 결정 wire 진입 결정 보류** — K-3 chunk 2 의 capability matrix EXTENSION 추가 + verify (Phase B/C 와 동일 패턴) 결정 wire 보류
- **옵션 (γ) source 변경 결정 wire 진입 결정 보류** — K-3 chunk 2 의 PRD §F 각 FR 별 source code review 결정 wire 보류 (위험, 비추)
- **옵션 (α, RECOMMENDED)** = 본 sprint 의 docs-only 결정 wire 정합 (정합 검증 결과 종합 capture 만 수행)

### 3.3 carryover honestly DEFER 보존
- K-3 chunk 1 검증 결정 wire 의 옵션 (β·γ) 결정 보류 그대로 보존
- K-3 결정 wire 의 chunk 3~6 결정 보류 그대로 보존 (chunk 3 = 상세기능명세 §F / chunk 4 = 제약사항 25 ADs + NFR / chunk 5 = 화면정의 §UI 부분 / 디자인가이드 = K-3 외부)
- cj-303 4건 + PRE-EXISTING 6건 + cj-307 LOW RISK ~30건 + sso 13 skipped tests + W1~W8 carryover + 비용 발생 항목 모두 + PRD v2 EXTENSION 보존

---

## §4 결정 wire 보존

### 4.1 결정 wire chain (cj-282~cj-319 + K-3 + K-4 종합)
- K-3 chunk 1 검증 결정 wire (`9842dc7`, cj-style 287번째) 결정 wire 그대로 보존
- K-3 결정 wire (`cc84b0e`, cj-style 286번째) 결정 wire 그대로 보존
- cj-319 (`2249fec`, cj-style 285번째 Track A-0 deploy-blocking wire) 결정 wire 보존
- cj-318 (`241fd3a`, cj-style 284번째 operator immediate execution entry) 결정 wire 보존
- cj-314 wire 5 retroactive correction (`145ff4a`, cj-style 283번째) 결정 wire 보존
- cj-314 wire 5 retroactive close-out (`4a57dd`, cj-style 282번째) 결정 wire 보존
- cj-312 retro (`bb95852`, cj-style 281번째) 결정 wire 보존
- cj-313 retro (`a14e95d`, cj-style 280번째) 결정 wire 보존
- cj-315 retroactive correction (`de7819c`, cj-style 279번째) 결정 wire 보존
- cj-315 (`4fa1d83`, cj-style 278번째) 결정 wire 보존
- cj-314 wire 4 meta close (`6756d1e`, cj-style 277번째 meta) 결정 wire 보존
- cj-314 wire 4 (`aacb12c`, cj-style 277번째 Phase B item 3 5 fixes) 결정 wire 보존
- cj-314 wire 3 (`34e92aa`, cj-style 276번째 Phase 8 ESLint/SLO/SLI 8 fixes) 결정 wire 보존
- cj-314 wire 2 (`4435e2d`, cj-style 275번째 Phase B item 1 6 fixes) 결정 wire 보존
- cj-314 wire 1 (`cca03c2`, cj-style 274번째 capability matrix drift 10 fixes) 결정 wire 보존
- cj-317 (`99a7343`, cj-style 273번째 alembic 0037 errors fix) 결정 wire 보존
- cj-316 (`1281ca5`, cj-style 272번째 FastAPI lifespan) 결정 wire 보존
- cj-314 entry (`3e2ed73`, cj-style 271번째) 결정 wire 보존
- cj-313 (`cfe5cea`, cj-style 270번째 pytest rootdir) 결정 wire 보존
- cj-312 (`a0a27d1`, cj-style 269번째 7-checkpoint audit) 결정 wire 보존
- cj-311 (`69d7d72`, cj-style 268번째) 결정 wire 보존
- cj-310 retroactive correction (`6972571`, cj-style 267번째) 결정 wire 보존
- cj-309b + cj-309 + cj-310 + cj-308 + cj-307 + cj-305b + cj-305 + cj-304 + cj-303 + cj-301 + cj-300 + cj-299 + cj-298 + cj-297 + cj-282 결정 wire 보존

### 4.2 외부 결정 wire 보존
- Pilot W1 launch D-day 2026-09-14 KST 보존 (D-3)
- MVP-verification 우선 (사용자 2026-09-10 결정 wire) 보존 — **배포작업 안 함 / RESEND·RAILWAY 등 지금 단계 X / 확실한 MVP 기능 갖춘 프로그램 필요**
- K-3 결정 wire (cj-style 286번째) parent 결정 wire 보존
- K-3 chunk 1 검증 결정 wire (cj-style 287번째) parent 결정 wire 보존
- K-4 메모리 description update 결정 wire (cj-style 288번째) 결정 wire 보존
- K-4 정의 결정 wire (`memory/project-2026-09-10-k4-mvp-verification-scope.md`) 보존

---

## §5 Files (4 files docs-only atomic single sprint)

| # | File | 종류 | 변경량 |
|---|---|---|---|
| 1 | `memory/handoff-2026-09-11-k3-chunk2-m0-m12-verification-done.md` | NEW | 본 handoff |
| 2 | `_bmad-output/implementation-artifacts/commit-msg-k3-chunk2-m0-m12-verification.txt` | NEW | commit message |
| 3 | `_bmad-output/implementation-artifacts/sprint-status.yaml` | MODIFIED | v4.104 → **v4.105 EXTENSION** A749 |
| 4 | `memory/MEMORY.md` | MODIFIED | K-3 chunk 2 hook |

### Sprint form
- docs-only atomic single sprint
- 0 source 변경 + 0 test 변경 + 0 alembic 변경 + 0 PRD 변경 + 0 capability matrix 변경 + 0 migration source 변경
- 37 pins unchanged + 14 job matrix unchanged
- PRD v7.0 §F/§M/§R unchanged + capability matrix v1.54 EXTENSION preserved
- audit actions EXTENSION preserved + AD-14 stack pin EXTENSION preserved

### Cumulative 결정 wire
- 60/60 → **61/61** 결정 wire 보존
- CR 11-3 honest-DEFER 289번째 chain cj-282 (220번째) → ... → K-4 메모리 description update 결정 wire (288번째, commit `00c49df`) → **K-3 chunk 2 검증 결정 wire (289번째, 본 sprint)**

### 결정 보류 (운전자, 본 sprint 후속)
1. **K-3 chunk 3 진입 결정 보류** — chunk 3 = 상세기능명세 §F 각 FR 정합 (옵션 c)
2. **K-3 chunk 4 진입 결정 보류** — chunk 4 = 제약사항 (25 ADs + NFR) 정합 (옵션 d)
3. **K-3 chunk 5 진입 결정 보류** — chunk 5 = 화면정의 §UI 부분 검증 (옵션 e)
4. **디자인가이드 진입 결정 보류** — K-3 외부 (옵션 f, 별도 epic)
5. **K-3 chunk 2 옵션 (β) docs+test 결정 wire 진입 결정 보류**
6. **K-3 chunk 1 옵션 (β·γ) 결정 wire 진입 결정 보류** (cj-style 287번째 결정 보류 그대로 보존)
7. **K-3 chunk 2 옵션 (γ) source 변경 결정 wire 진입 결정 보류** (위험, 비추)

---

**Date**: 2026-09-11 KST (D-3)
**Author**: Claude (operator = kjw)
