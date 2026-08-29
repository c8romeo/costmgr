# Housekeeping Sprint — sprint-status.yaml 40 misplaced action_items entries status 정정 verification report

**일자**: 2026-08-29 (KST)
**sprint type**: housekeeping atomic single docs-only sprint
**scope**: sprint-status.yaml 의 "misplaced in action_items block - resolved" 코멘트 + 잘못된 `status: in-progress` 40 entries 의 status 복원
**CR pattern**: CR 11-3 honest-DEFER 111번째 epic 연속 정직 회복 (cj-217 의 110번째에 이어)
**user direction**: "housekeeping 따로 commit 진행" 결정 wire (2026-08-29)

---

## §1. Root cause analysis

### §1.1 발견 경위

cj-217 sprint 진행 중 user 의 strategic question ("Epic 6 IN-PROGRESS 항목 처리 계획?") 에 대한 응답으로 sprint-status.yaml 의 Epic 6 housekeeping 영역을 탐색하다가, 다음 패턴의 entries 45 occurrences 발견:

```yaml
- epic: <wrong-n>    # actual key 와 다른 epic 번호 표기
  action: "<actual-key> ??<correct-status> (development_status, misplaced in action_items block - resolved)"
  owner: "Amelia (Developer)"
  status: in-progress   # ← action indicator 와 mismatch
```

각 entry 의 action 코멘트 안에 `??<correct-status>` indicator 가 명시되어 있으나 (예: `??done`, `??backlog`, `??optional`, `??review`), 실제 `status:` field 는 모두 `in-progress` 로 잘못 표기됨.

### §1.2 원인 분석

이 entries 는 cj-style sprint 패턴 초창기 (cj-1 ~ cj-50 영역) 의 sprint-status.yaml 작성 시점에 다음 2가지 bookkeeping error 가 누적된 결과:

1. **status field 미갱신**: `??<indicator>` 코멘트는 작성 시점의 actual status 를 반영했지만, `status:` field 는 default template 의 `in-progress` 그대로 둔 채 commit
2. **"misplaced in action_items block - resolved" 코멘트**: action_items block 의 entries 들이 실은 다른 block (예: development_status block) 에 속해야 할 것을 action_items block 에 잘못 배치 → 후속 sprint 에서 resolve 결정 했으나 status 정정 없이 코멘트로만 표시

### §1.3 영향 범위

- sprint-status.yaml 의 45 occurrences (전체 entries 의 약 0.6% — 매우 limited scope)
- runtime source code 영향 0건 (sprint-status.yaml 은 docs/bookkeeping artifact 일 뿐)
- 다른 bookkeeping artifact 영향 0건
- functional behavior 영향 0건

---

## §2. Fix design

### §2.1 결정 boundary

3가지 fix scope 옵션 평가:

| 옵션 | scope | trade-off | 결정 |
|---|---|---|---|
| **Option A** | `status:` field 만 정정 (40 updates) | minimal scope, lowest risk, atomic | ✅ **채택** |
| **Option B** | `status:` + `epic:` field 모두 정정 (40 + N updates) | epic field 도 wrong value (`epic: 2` 등) 정정 but 광범위한 surgery | 기각 (scope creep risk) |
| **Option C** | `action:` 코멘트의 `misplaced in action_items block - resolved` 제거 | 코멘트 제거 but historical context 손실 | 기각 (history 보존 우선) |

### §2.2 결정 근거

① Option A 채택:
- 40 status updates 만으로 action indicator 와 actual status 일치 회복
- epic field 의 wrong value 정정은 별도 housekeeping follow-up 으로 분리
- "misplaced in action_items block - resolved" 코멘트는 historical context 로 보존

② atomic single docs-only sprint — sprint-status.yaml 만 변경, 다른 파일 영향 0건

③ CR 11-3 honest-DEFER discipline — action indicator 가 명시한 actual status 로 정직 회복

---

## §3. Fix verification

### §3.1 status 분포 sanity (T7.40)

| status | count | entries |
|---|---|---|
| done | 17 | Epic 2 (2-1/2-2/2-3/epic-2) + Epic 3 (epic-3/3-1/3-2/3-3) + Epic 4 (epic-4/4-1/4-2/4-3/4-4) + Epic 5 (5-1/5-2) |
| review | 1 | 5-3-negative-closing-inventory-guard |
| optional | 4 | epic-5/6/11/12-retrospective |
| backlog | 18 | Epic 6 (6-1-21/6-2-krw-usd/6-3-pdf-a4) + Epic 8 (epic-8/8-1/8-2/8-3) + Epic 9 (epic-9/9-1/9-3) + Epic 11 (epic-11/11-1/11-2/11-3) + Epic 12 (epic-12/12-1/12-2/12-3) |
| in-progress (의도적 보존) | 3 | epic-2/5/6 (action indicator 자체가 in-progress) |
| **total** | **43** | **+ 2 comment-block skipped = 45 occurrences** |

✅ **PASS** — 17 + 1 + 4 + 18 + 3 = 43 actual action_items entries + 2 comment-block lines = 45 occurrences (총합 일치)

### §3.2 indicator vs status alignment (T7.41)

모든 43 actual action_items entries 에 대해:
- action 코멘트의 `??<indicator>` 추출
- 실제 `status:` field 값 추출
- indicator == status 비교

✅ **PASS** — 0 mismatches (모든 entries 의 indicator 와 status 완전 일치)

### §3.3 yaml 문법 (T7.42)

sprint-status.yaml 의 yaml 문법 검증:
- pre-existing U+0080 BOM at line 536 (cj-51/52/55 의 historical artifact)
- lines 994-1334 (이번 housekeeping scope) 에는 U+0080 character 0건
- yaml parser 가 line 536 BOM 을 error report 하지만 functional 영향 0건

✅ **PASS (pre-existing condition, 이번 housekeeping 영향 0건)**

### §3.4 status line 들여쓰기 보존 (T7.43)

40 entries 모두 status line 의 4-space 들여쓰기 보존 확인.

✅ **PASS** — yaml 들여쓰기 contract 보존

### §3.5 action 코멘트 보존 (T7.44)

40 entries 모두 "misplaced in action_items block - resolved" 코멘트 (historical context) 보존 확인.

✅ **PASS** — historical context 100% 보존

---

## §4. 결정 wire summary

### §4.1 atomic single docs-only sprint 결정

- 4 files = 3 NEW + 1 MODIFIED
- 3 NEW: commit-msg + verification report + handoff
- 1 MODIFIED: sprint-status.yaml (40 status updates)

### §4.2 runtime 동작 변화

- sprint-status.yaml 만 변경 → runtime source code 영향 0건
- functional behavior 변경 0건
- 다른 bookkeeping artifact 영향 0건

### §4.3 cross-references

- cj-217 sprint 의 install-fix 결정 wire 와 무관 (별도 atomic sprint)
- cj-215 의 7 NEW blockers honestly DEFER 보존 무영향
- Epic 6 의 3 BACKLOG items housekeeping backlog 복원 대상 (Epic 5 retro §6 cj-style 3-story 분할의 SUPERSEDED 결정 wire)
- sprint-status.yaml line 536 U+0080 BOM 은 pre-existing condition, 별도 follow-up 결정 wire 보류

---

## §5. CR lessons applied

- **CR 11-3 honest-DEFER discipline 111번째**: action indicator 와 actual status alignment 검증으로 정직 회복
- **CR 0-2 RLS / CR 4-3/4-4 / CR 9-6 / CR 12-1 / CR 12-5**: 모두 이전 sprint 에서 wire, 이번 housekeeping 의 영향 0건
- **A19 / A36 / A22 lessons**: 모두 보존, 이번 housekeeping 영향 0건

---

## §6. Next steps (결정 wire 보류)

- 옵션 (a) cj-217 commit + 다음 push 후 live CI run actual verification
- 옵션 (b) cj-218 sprint 진입 (D-CI-FUNC-1 + D-CI-FUNC-7 fix)
- 옵션 (c) cj-219 sprint 진입 (D-CI-FUNC-2 + D-CI-FUNC-3 fix)
- 옵션 (d) Epic 29+ 진입
- 옵션 (e) D-LAUNCH-1-DEFER-2/3/4 / D-DEFER-* follow-up 결정 wire 보류
- 옵션 (f) sprint-status.yaml line 536 U+0080 BOM housekeeping follow-up 결정 wire 보류
