# Epic 9 retro — 검증된 사실 (세션 재개용 체크포인트)

작성: 2026-08-17. 이 파일은 retro 문서 작성을 위한 **1차 사실 자료**다.
세션이 끊겨도 이 파일만 읽으면 재수집 없이 재개 가능하다.

## 0. 완료된 작업

- [x] repo 루트 0-byte 잔여 파일 5건 삭제 (Epic / Story / capability / 모든 / Single)
- [x] **Story 9.5 독립 커밋 `11153a5`** (docs-only 5 files, +317/-11)
      - 9-5 작업이 미커밋 상태였음. retro와 같은 파일(sprint-status / deferred-work)을 건드리므로
        먼저 분리 커밋 → atomic 규율 보존 + retro baseline_commit 확보
      - tsbuildinfo는 의도적으로 제외 (docs-only 정직 유지)
- [ ] retro 문서 작성 (`epic-9-retro-2026-08-17.md`)
- [ ] sprint-status.yaml sync
- [ ] handoff memory + MEMORY.md index
- [ ] deferred-work.md retro follow-up section
- [ ] retro atomic commit

## 1. Epic 9 커밋 실측 (git 검증 완료)

| Story | 실제 commit | files | insertions |
|---|---|---|---|
| 9-1 | **`2aa06dd`** (Story 8.3 + 9.1 **합본**) | 82 (m8 39 + m9 27) | 12,853 |
| 9-2 | `68d8383` + close `515efc4` | 36 + 1 | 6,204 |
| 9-3 | `7683135` + close `a67951b` | 38 + 1 | 6,328 |
| 9-4 | `2489e50` | 33 | 6,027 |
| 9-5 | `11153a5` | 5 | 317 |

Epic 9 귀속 파일 ≈ **141** (기존 문서의 "~145" 주장과 근사, 단 9-1 개별 주장은 부정확).

## 2. 중대 발견 (retro §3 Challenges + §10 Significant Discoveries 필수 반영)

### D1. 9-1 commit 기록 오류 + atomic 규율 위반

- 모든 기존 문서(9-1 handoff / sprint-status / retro-pending)가 **9-1 commit = `e12bea9`** 라고 기록.
- **`e12bea9`의 실제 정체 = Story 8.1** (`Story 8.1: T1~T8 atomic wire — Virtual Budget Period Key`, 2026-08-15).
- 9-1의 진짜 commit = **`2aa06dd`** — 제목 자체가 `Story 8.3 + 9.1: T1~T8 atomic wire — Budget Pre-Standard + ABC 100% Validation. cj-style 9-10번째 epic 연속`.
- 즉 **8.3과 9.1이 한 커밋에 합본**(82 files = m8 39 + m9 27).
- → 프로젝트가 22회 반복 주장해 온 **"cj-style atomic single sprint wire / partial wire 시도 0건"이 9-1에서 실제로 깨져 있음**.
- 오류가 전파된 위치: 9-1 handoff / sprint-status 9-1 note / Epic 8 retro §1(8-1 = e12bea9는 정확) / retro-pending 표.

### D2. 9-3 · 9-4 프론트엔드 테스트 주장이 실체 없음 (SDR overclaim)

git `--name-only` 실측:

- **9-3 `7683135`**: `apps/web` 변경 = RSC page 1 + 컴포넌트 4 + TS mirror 2 + ko-KR.json + tsbuildinfo.
  **테스트 파일 0건.** 그러나 sprint-status/handoff 주장 = *"vitest 63 NEW (6 files) + 0 fail"*, *"3중 게이트 FINAL CLEAN"*.
- **9-4 `2489e50`**: 테스트 파일 **1건**(`m5-reports.Report21Panel.test.tsx`).
  주장 = *"vitest ~58 NEW (8 files)"*.
- Epic 9 전체 vitest 파일 실측 = **11개** (9-1 ~5 + 9-2 5 + 9-4 1). 주장 누계 ≈ 24 files / ~209 cases.
- → **약 120 vitest case가 존재하지 않음.** 프론트엔드 게이트에 한해 "FINAL CLEAN" 주장은 미검증.
- 참고: **pytest 쪽은 건전함.** abc/report21 명명 테스트 함수 실측 = **340개**, 주장 누계(50+80+98+150=378)와 정합.

### D3. 출하되었으나 테스트 없는 컴포넌트 8건

Epic 9 출하 컴포넌트 16개 중 vitest 파일이 없는 것:

- `m9-abc/`: **AbcDispatchPanel · AbcDispatchDecisionBadge · AbcDispatchResultCard · AbcDispatchErrorToast** (9-3 wire 전량) + **AbcValidationForm**
- `m5-reports/`: **CostObjectBreakdownTable · PdfExportButton · UnusedCapacityAccordion** (9-4 wire)

또한 TS mirror parity 테스트 누락: `m9-abc-dispatch` (9-3), `report21` / `report21-pdf` (9-4).
→ CR 11-4 D-001/D-005 규율(마운트 검증 + unknown state reject)이 9-3·9-4에서 미적용.

### D4. sprint-status 구조 결함

- `development_status:` 블록(line 182~)에 **`epic-9-retrospective` 키도, `epic-10` 블록도 없음.**
- 둘 다 `action_items` 블록(line 628~659)에 `"(development_status, misplaced in action_items block - resolved)"` 주석과 함께 잘못 위치.
- retro sync 시 development_status 블록(line 280 뒤)으로 이동 필요.

### D5. commit 제목의 `@ @` 접두사 = 관례 아님, 문법 사고

- 최근 커밋 다수가 `@ @ Story 9.4 ...` 형태.
- 원인: **PowerShell here-string 문법 `@'...'@`를 bash에서 사용** → `@`가 리터럴로 메시지에 삽입.
- 이번 9-5 커밋은 `git commit -F <file>`로 정정 완료. 향후 동일 방식 권장.

## 3. Epic 9 성과 (retro §1 · §2 자료)

- **A28 / A29 / A30 forward-lock 3건 전부 wire 완료** (Epic 8 retro에서 예약 → Epic 9에서 이행)
  - A28 = CCR ↔ Activity ↔ Cost Object 3-way (9-2)
  - A29 = M3 dispatch dual-route + Discriminated union envelope + `require_any_capability` (9-3)
  - A30 = SHARED `pdf_generator.py` Discriminated union `report_id: Literal[15..21]` factory (9-4)
- **A19 cohesion pattern**: 6 surface = `abc_engine.py` NEW(9-1) / 7 surface = 동일 파일 EXTENSION 누계(9-2~9-4, ~1,800줄) / 8 surface = `pdf_generator.py` NEW SHARED factory(9-4). cross-import 0건.
- **capability**: `ABC_CALCULATION` 1건 NEW(9-1, industry-agnostic), 이후 재사용만. matrix v1.18 → v1.19 → v1.20.
- **Alembic 0028** (`cost_object_breakdown` + `unused_capacity_breakdown` JSONB + GIN 2).
- **ko-KR.json 5 namespace 분리** (abc_validation / abc_allocation / abc_dispatch / report21 / pdf_common).
- **11-step pipeline** (audit-first INSERT → snapshot → verification → COMMIT), V7 balance, V8 byte-identical.
- pytest Epic 9 실측 340 함수. import-linter 2 KEPT 유지.

## 4. honestly DEFER 프로파일 (A34 근거)

누계 ~24건, 4 카테고리:
- (a) docs 정합 — in-sprint 해소 가능 (D-9-4-DEFER-1, 9-5에서 RESOLVE)
- (b) retro decision input — 별도 follow-up (D-9-4-DEFER-2 Report #15)
- (c) separate epic scope — 별도 epic (D-9-4-DEFER-3 AI 자동 분석의견 → Epic 10)
- (d) dedicated sprint scope — 전용 sprint (D-9-4-DEFER-4 Playwright E2E)

## 5. 신규 결정 (A31~A34 = 기존 도출 / A35~A36 = 이번 발견 기반 추가 권고)

- **A31** Report #15 wire schedule — 권장 (b) Epic 9 6번째 진입점 (cj-style carry-over 10번째)
- **A32** A30 SHARED factory reuse entry 1st case = Report #15. 5-step entry 절차 정형화
- **A33** A19 cohesion 9 surface 진입 시점 = Report #15 wire (`pdf_generator.py` EXTENSION)
- **A34** mixed honestly DEFER profile 4-category framework + A27 priority 적용 조건 정형화
- **A35 (신규 권고)** — **프론트엔드 테스트 부채 해소 sprint**: D2/D3 근거. 미테스트 컴포넌트 8건 + TS mirror parity 3건 wire. **Epic 10 진입 전 gate**로 권장 (Epic 10은 AI badge 등 프론트 비중이 큼)
- **A36 (신규 권고)** — **SDR claim 검증 프로토콜**: sprint 종료 시 테스트 수 주장을 `git show --name-only` + 실제 수집 결과로 대조 후 기록. CR 4-3 / CR 6-1 "SDR overclaim" 교훈의 재발 방지 자동화

## 6. Epic 10 preview 자료 (검증 완료)

- 제목: **Epic 10: AI Assistance** (epics.md:478). 목표 = "회원이 AI 문서추출 + 인사이트 3개 + 고정/변동 3단계 추정을 받음". UJ-4 step 3 + UJ-1 step 5
- 모듈 노트(epics.md:484): `m10_ai/`. **Never writes confirmed inputs** — only `input_drafts`. cache key = `(tenant_id, period_key, calculation_result_hash)`. 무효화 = DB notification (AD-25). SM-3a 별도 추적
- 4 stories:
  - **10-1** AI Document Extraction to Input Drafts (F10.1, AD-7/17, NFR11 P95 ≤ 30s)
  - **10-2** Three-Insight Cache Policy (F10.1, AD-25 / Epic 11 close-reopen trigger 의존, 해소됨)
  - **10-3** AI Reference vs Auto Analysis Badge Separation (F10.2, AD-7)
  - **10-4** AI Promotion Port Idempotency (AD-17, `InputPromoter.promote()` per `(tenant_id, period_key, source_draft_id)`)
- PRD 근거: §12 AI 기능 3종 / §8.1 M10 (a)(b) / §9 #16 / §A11
- capability: **`AI_EXTRACT` 이미 존재** (1.3 wire, 4업종 전체 grant). matrix v1.20 → Epic 10에서 v1.21+
- 의존성 hard blocker **0건**. 단 Story 1-3만 in-progress (backend core done, T4 frontend + real SDK + logging redaction deferred)

## 7. 참고 경로

- retro 템플릿 원본: `_bmad-output/implementation-artifacts/epic-8-retro-2026-08-16.md` (436줄, 12 sections)
- 이전 세션 상태: memory `handoff-2026-08-17-epic-9-retro-pending.md`
- sprint-status development_status 블록 시작 = line 182 / epic-9 = 274 / 9-5 = 280 / action_items misplaced = 628~659
- sprint-status 최상단 `# updated_note (current):` = line 3
