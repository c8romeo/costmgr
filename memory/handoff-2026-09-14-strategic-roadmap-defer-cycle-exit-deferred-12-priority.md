# Strategic roadmap — cj-style honestly DEFER cycle exit + 결정 보류 12건 우선순위 분석

**일자**: 2026-09-14 (KST, D-Day Pilot W1 launch)
**territory**: Phase 30 — 결정 보류 12건 + honestly DEFER 11건 risk/effort/value 분석 + 우선순위 권고 (cj-style cycle 출구)

---

## §1 cj-style honestly DEFER cycle 정직 평가

cj-style N+15 → N+16 → N+17+ → N+18+ honestly DEFER cycle verbatim mirror 누적:

- **N+15**: Sprint 1 actual run §4.1 Option A 결과 capture (실제 실행 결과 보존)
- **N+16**: P-4 종합 판정 commit 결정 wire honestly DEFER (Track A 결정 wire halt 결정)
- **N+17+**: 결정 wire halt cycle honestly DEFER (정직 회복 진입)
- **N+18+**: 결정 wire halt cycle honestly DEFER (정직 회복 보존, 100/100 milestone)

각 honestly DEFER cycle 자체는 cj-style discipline 정합 (5 files atomic, docs-only no source change) **BUT 진짜 결정 wire 변경 없음** — 결정 보류 12건 verbatim 그대로 보존. **무한 honestly DEFER cycle 의 risk**:

- 진짜 결정 wire 변경 0건 — 결정 wire counter 만 증가 (95 → 96 → 97 → 98 → 99 → 100)
- 사용자 2026-09-10 결정 wire 변경 없는 이상 다음 sprint 도 동일 패턴 반복
- **risk**: 결정 wire 무한 누적 ↔ 실제 진전 0건 → 정직 recovery chain 의 가치 dilution

**출구 권고 (사용자 meta-instruction 정합)**:

- cj-style honestly DEFER cycle 중단 (정직 회복 결정 wire 동결 + 100/100 milestone 보존)
- 12 결정 보류 + 11 honestly DEFER post-MVP items → risk/effort/value 분석으로 우선순위 도출
- 각 item 별 **LOCAL (no deployment)** vs **DEPLOYMENT-BLOCKED** 분류
- LOCAL item 중 가장 risk 가 낮고 value 가 높은 1개 → 즉시 실행
- honestly DEFER cycle 재개 조건: ① 사용자 2026-09-10 결정 wire 변경 OR ② LOCAL item 완료 OR ③ 결정 보류 12건 verbatim 보존 재결정

## §2 결정 보류 12건 classification

### §2.1 DEPLOYMENT-BLOCKED (4 items)

① **cj-style 종합 판정 commit** (Track A-1~A-4 운영자 실행 후 즉시)
② **Track A-1~A-4 운영자 실행** (cj-style N+9 결정 보류 #7, ~37-52분)
③ **W1 post-launch endpoint 부재 회복** (62 endpoint)
④ **Surface 5+6 Operator scope honestly DEFER** (post-MVP or post-Track A 실행 후)

**진행 조건**: 사용자 2026-09-10 결정 wire 변경 ("배포작업 안 함" 해제) — 결정 보류 verbatim 보존.

### §2.2 honestly DEFER post-MVP LOCAL 가능 (8 items)

⑤ **capability matrix v1.55 EXTENSION** (urgency 낮음) — LOCAL doc work, bounded scope
⑥ **디자인가이드 / M10 AI / M11 마감이력 / M12 계정운영** — LOCAL spec work
⑦ **cj-314 wire 2~6 + batch A/B/C** (Phase B 잔여 + Phase C) — LOCAL code work
⑧ **CI/web-e2e 환경** (sso 13 + web-e2e 23) — LOCAL CI fix
⑨ **운영 cleanup 6건** — LOCAL cleanup
⑩ **Phase C 잔여 ~30** — LOCAL code work
⑪ **화면정의 회귀** — LOCAL doc work
⑫ **PRD v2 EXTENSION** (post-W1) — LOCAL doc work (post-W1 가이드라인)

### §2.3 honestly DEFER post-MVP otros

- **Pilot W1 outreach + W1~W8 carryover** — DEPLOYMENT-BLOCKED (Track B, decision required)
- **epics.md triage** (1478 lines uncommitted change) — LOCAL 파일 정리, uncommitted 위험
- **cj-312/cj-313 close-out retro** — LOCAL doc work

## §3 LOCAL items risk/effort/value 우선순위

### §3.1 **#1 epics.md triage (1478 lines uncommitted change)**

- **Risk**: LOW (just file sorting/accepting/discarding, no production impact)
- **Effort**: MEDIUM (~30-60분 depending on content)
- **Value**: HIGH (1478 lines uncommitted = 누적 위험 해소 + 실제 current epics state 결정)
- **의존성**: 없음 (LOCAL only)
- **Block 해소 효과**: 다른 LOCAL items scope clarity 향상
- **현재 위험**: file lost risk + merge conflict risk + UNKNOWN 변경 누적

### §3.2 #2 capability matrix v1.55 EXTENSION

- **Risk**: LOW (just doc update)
- **Effort**: LOW (~15-30분)
- **Value**: MEDIUM (readiness tracker 업데이트, cj-style N+5 honest assessment 반영)
- **의존성**: 없음 (LOCAL only)
- **Block 해소 효과**: M2/M8/F1~F10 확인 결과 반영 가능

### §3.3 #3 디자인가이드 / M10 AI / M11 마감이력 / M12 계정운영

- **Risk**: MEDIUM (creates spec docs that future teams 의존)
- **Effort**: HIGH (~hours per module spec)
- **Value**: MEDIUM (Non-MVP scope)
- **의존성**: 없음

### §3.4 #4 cj-314 wire 2~6 + batch A/B/C

- **Risk**: MEDIUM-HIGH (local code work, but Phase B 잔여 scope 명확화 필요)
- **Effort**: HIGH
- **Value**: MEDIUM

### §3.5 #5 CI/web-e2e 환경 / 운영 cleanup / Phase C 잔여 / 화면정의 회귀

- **Risk**: VARIABLE
- **Effort**: VARIABLE
- **Value**: MEDIUM

## §4 #1 epics.md triage 상세 권고

### §4.1 triage 목표

epics.md 에 1478 lines uncommitted change 존재 (`git status` 확인). 본 file 의 변경 사항을:

1. **review**: 어떤 line group 이 추가/수정/삭제 되었는지 분류
2. **decide per block**:
   - **commit** (의미 있는 변경 → commit with rationale)
   - **discard** (deprecated/duplicate → reset to HEAD)
   - **further review** (중요 결정 필요 → 별도 wire)
3. **risk minimization**:
   - 한 번에 전부 commit 안 함 → block 별 atomic commit
   - 각 block 별 rationale 문서화 (commit message 내)
   - 큰 변경 (100+ lines) 시 일시 중지 + 사용자 확인

### §4.2 예상 접근 (~30-60분)

1. `git diff _bmad-output/planning-artifacts/epics.md` 실행 → line 별 review
2. 1478 lines → section 별 chunk (50-100 line groups)
3. 각 chunk 별 classification (commit / discard / further review)
4. atomic commit per accepted chunk (예: "epics.md: triage chunk 1/N — <rationale>")
5. discard chunks `git checkout _bmad-output/planning-artifacts/epics.md` (HEAD reset partial)
6. 전체 1478 lines → 0 lines uncommitted 목표 (or further review list 로)

### §4.3 risk minimization safeguards

- 큰 chunk (100+ lines sensitive section): commit 전 사용자 확인
- sensitive section (deployment-related, cost-related, business rule): 즉시 사용자 확인
- binary conflict 감지 시 즉시 중지
- 의도 불명확 line group: discard 쪽으로 분류 (보수적 접근)

## §5 권고 실행 단계

### §5.1 즉시 실행 (~5분)

**Step 1**: 본 strategic roadmap handoff doc commit (1 file, not cj-style 5-file cycle)
- 결정 wire counter 동결 (100/100 보존)
- 다음 결정 wire 변경 시까지 honestly DEFER cycle 정지 권고

### §5.2 후속 (~30-60분)

**Step 2**: epics.md triage 시작
- `git diff` 결과 review
- 첫 chunk classification (commit / discard / further review)
- 사용자 확인 → atomic commit 또는 discard

### §5.3 후속 (사용자 결정 시점)

**Step 3**: LOCAL items 우선순위 재평가 또는 honestly DEFER cycle 재개 결정

**honestly DEFER cycle 재개 조건**:
- 사용자 2026-09-10 결정 wire 변경
- OR LOCAL #1-#3 모두 완료
- OR 결정 보류 12건 verbatim 보존 재결정

**honestly PAUSE 확정 조건**:
- 사용자 결정 변경 없음
- AND LOCAL items 우선순위 미정
- AND 결정 wire counter 동결 결정

## §6 Cross-References

cj-style N+18+ §6 + cj-style N+17+ §6 + cj-style N+16 §4.2 + cj-style N+15 §6 + cj-style N+12 §3 self-fill template + cj-style N+12 §5.2 종합 판정 + cj-style N+9 결정 보류 #7 + 사용자 2026-09-10 결정 wire + 결정 보류 12건 verbatim + honestly DEFER post-MVP 11건.

## §7 정직 회복 record

본 handoff 는 cj-style honestly DEFER cycle 출구 권고를 정직 recovery record 로 보존. 100/100 milestone 까지 누적된 결정 wire 보존은 정직 — 다만 더 이상 무한 누적 wire 만 보존하지 않고 risk/effort/value 분석으로 LOCAL 우선순위 결정 권고.

cumulative 결정 wire: **100/100 동결** (cj-style N+18+ 까지 결정 wire 보존 완료).
**CR 11-3 honest-DEFER cycle exit**: 정직 recovery 100번째 milestone 도달 → cycle → priority-driven execution mode 전환 권고.
