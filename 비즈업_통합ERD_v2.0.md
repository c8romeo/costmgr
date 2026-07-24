# 비즈업(Biz-Up) 통합 데이터베이스 설계(ERD) v2.0
## 전통 개별원가 엔진 + ABC 엔진 통합판

| 항목 | 내용 |
|------|------|
| 문서 버전 | **v2.0 (통합·확정)** — 비즈업 ERD v1.0 + ABC모듈 ERD v1.0 + 테이블명세서 v1.0을 **완전 대체** |
| 작성일 | 2026-07-12 |
| DB | PostgreSQL 15+ (Supabase, RLS 멀티테넌트) |
| 총 객체 | **테이블 66개(12개 도메인) + 파생 뷰 3개** |
| 근거 문서 | 통합 PRD v2.0 (회계 공리 헌장 A1~A11, 결정 Q-A~Q-J) |
| v1.0 대비 | 신규 2 테이블(+order_records, +reconciliation_results) / 폐지 1(−budgets) / 재편 2(resource_pools·pool_activity_assignments → pool_basis_ratios·activity_basis_shares) / 컬럼 변경 다수 (제10장 변경 대장) |

> v1.0 총괄표의 표기 오류(47로 표기, 실제 도메인 합산 49)를 본 문서에서 재계수하여 확정한다.

---

# 1. 최상위 설계 원칙 — 회계 공리의 DB 구현 매핑

**통합 PRD v2.0 제3장(회계 공리 헌장)이 본 ERD의 최상위 규범이다. 각 공리가 어느 DB 장치로 강제되는지 명시한다.**

| 공리 | 내용 | DB 구현 장치 |
|------|------|-------------|
| A1 발생주의·기간귀속 | 월 귀속, 마감 후 불변 | `fiscal_periods` 상태 전이 + 월별 테이블 공통 마감잠금 트리거 |
| A2 제조원가/판관비 구분 | 판관비는 재고 불산입 | `product_costs`의 2계층 컬럼 분리(`manufacturing_*` vs `full_*`), 재고 평가는 manufacturing만 참조 |
| A3 월총평균법 | 기중 변경 금지 | `inventory_balances.avg_unit_cost` 단일 산식, 평가방법 설정 자체를 두지 않음(하드코딩) |
| A4 생산기준 배부 | 매출기준 배부 폐기 | `costing_settings.alloc_population = 'production'` 고정(CHECK 단일값) + 재고조정 자동화(`reconciliation_results`) |
| A5 인과관계 배부 | 배부기준 3종 택1 | `costing_settings.overhead_alloc_basis` CHECK 3종, 월별 재정의(`alloc_basis_override`) **폐지** |
| A6 완전배부(Zero-Leak) | 배부합계=원금액 1원 단위 | `cost_allocations`·`segment_allocations`·ABC 각 단계의 트랜잭션 내 합계 검증, 불일치 시 전체 롤백 |
| A7 일관성·전진법 | 기중 변경 금지 | 설정류 `effective_fiscal_year` 발효 필드, BOM `effective_from`+스냅샷, 마감분 불변 |
| A8 검증가능성 | append-only·역분개·스냅샷 | `inventory_ledger` UPDATE/DELETE 금지 정책, `bom_snapshots`·`process_snapshots`, `audit_logs` |
| A9 유휴능력 별도 관리 | 제품 배부 금지 | `abc_unused_capacity`(used+unused=practical 항등식) + `work_calendars` 차이시간 금액화 — 어느 배부 테이블에도 유휴원가 유입 경로 없음 |
| A10 공통원가 자의배부 금지 | 세법 2기준만 | `segment_allocations.basis_used` CHECK 2종('revenue','individual_cost') |
| A11 오류 가시화 | 경고→마감 차단 | `validation_warnings.severity`(warning/blocking) + blocking 존재 시 close 거부 트리거 |

---

# 2. 통합 데이터 흐름 — 월 사이클

```
[월별 입력] order(선택)·sales·purchase·production·labor·expense_records + work_calendars
    ↓ (부문 보유 ③④ 고객) 부문 분할 실행
[부문분할] segment_allocations — 계정별 세법 2기준, 합계=원금액 롤백 검증 [A6·A10]
    ↓ [원가계산 실행] 버튼 (E11 계산 버튼 방식)
[스냅샷 고정] bom_snapshots + process_snapshots (전진법 [A7])
[원장 기록] inventory_ledger (append-only [A8])
[재고 평가] inventory_balances (월총평균법 [A3])
[제조 원가] product_costs(2계층 [A2]) + cost_allocations(생산기준 [A4], 배부합계 검증 [A6])
[검증·조정] reconciliation_results — check 4요소 자동 분해 → '제품 재고 조정' 라인 [A4·A11]
    ↓ (서비스 부문 보유 시)
[ABC 계산] abc_runs — classic 3-Step 또는 TDABC, 완전배부·항등식 검증 [A6·A9]
    ↓
[AI 큐레이션] ai_insights (질문 3개 캐시, module 구분)
[공동 마감] fiscal_periods.close — blocking 경고 0 + 부문분할·제조·ABC 완료 필수, 기말→익월 기초 이월
```

예산 사이클: `period_type='budget'` 가상 기간에 동일 입력 체계로 계획치 입력 → 사전 표준원가계산 → 실적 기간과 자동 대조(pl5 재현). 예산 기간은 재고 체인·마감 체인에서 제외.

---

# 3. 도메인 A. 테넌트·계정·보안 (7)

v1.0 구조 유지. tenants, users, login_notification_recipients, login_events, proxy_access_consents, audit_logs, announcements.

**v2.0 변경 — tenants 확장 (ABC ERD의 확장 5건 본선 편입):**

| 컬럼 | 타입/제약 | 설명 |
|------|----------|------|
| industry_selection | TEXT CHECK (IN ('mfg','svc','mfg_svc','mfg_svc_other')) | 업종 4지선다 |
| has_manufacturing / has_service / has_other | BOOLEAN | 파생 플래그 (엔진·메뉴 노출 제어) |
| base_currency / fiscal_start_month | 기존 | E6·E11 유지 |

RLS 표준 정책(테넌트 격리 + 운영자 대리접속 SELECT 전용)은 v1.0 규약 전면 상속.

---

# 4. 도메인 B·C. 구독·기초정보 마스터 (10)

**B. 구독 (2)**: subscriptions, cancellation_requests — v1.0 유지.

**C. 마스터 (8)**: items, units, item_unit_conversions, partners, departments, processes, expense_accounts, exchange_rates.

v2.0 확정 사항:

| 테이블 | v2.0 내용 |
|--------|-----------|
| **items** | item_type 5분류 확정: product / semi_product / raw_material / **merchandise**(유통 상품 — BOM 자기참조 1 마이그레이션 시 자동 변환) / **service**(서비스상품, 재고 없음). `production_method_id` FK(생산유형 상속). 유통품 3규칙(노무 배부 제외·공수 미산정·간접 귀속)은 엔진 규칙으로 item_type='merchandise' 분기 |
| **departments** | labor_type(직접/간접) + `labor_cost_behavior`(직접=변동/간접=고정 기본, 재정의 허용) — BEP·차월추정의 인건비 성격 원천 |
| **expense_accounts** | cost_behavior(고정/변동) + behavior_source 3단계 추정 전이(E12) + `expense_class` CHECK ('manufacturing','sga','**non_operating**') + `segment_attribution`(mfg_only/svc_only/other_only/common — 카브아웃 태깅) |
| **processes** | 공정 마스터 — production_methods·method_process_shares와 연결 |

---

# 5. 도메인 D. BOM·공정·생산유형 (6)

bom_lines, bom_snapshots, product_processes, process_snapshots, production_methods, method_process_shares — v1.0 유지.

핵심 메커니즘 재확인:
- **전진법**: bom_lines.effective_from + 계산 시 bom_snapshots 고정 [A7·A8]
- **production_methods**: 생산유형 ≤15, 표준공수 = 작업인원 × 작업시간 ÷ 작업수량 (원본 process 재현)
- **method_process_shares**: 유형별 공정 ≤10, SUM(share_ratio)=100% 시스템 강제
- **공수 파생 우선순위**: 제품별 정의(product_processes) 우선 → 없으면 생산유형 상속 (하이브리드)

---

# 6. 도메인 E. 회계기간·월별 데이터 (11)

### E1. fiscal_periods — 회계기간 (v2.0 핵심 확장: 예산 시나리오)

| 컬럼 | 타입/제약 | 설명 |
|------|----------|------|
| fiscal_year / seq_in_year | INT | 회계연도 가변(E6) |
| **period_type** | TEXT NOT NULL DEFAULT 'actual' CHECK (IN ('actual','**budget**')) | **예산 시나리오 = 가상 기간** (원본 13번째 저장공간의 승격, 결정 Q-D). 회계연도당 budget 세트 1식 |
| status | not_started→open→calculated→closed | actual 전용. **budget 기간은 마감 체인·재고 이월 체인에서 제외**(closed 불요, 언제든 수정) |
| segment_alloc_done / mfg_calc_done / abc_calc_done | BOOLEAN | 마감 일원화 선행 플래그 |
| UNIQUE | (tenant_id, fiscal_year, seq_in_year, period_type) | 실적·예산 병렬 존재 |

순차입력 강제(이전 월 closed 필수)·마감잠금 트리거는 actual에만 적용.

### E2~E5. 월 거래 4종 — 공통 패턴: 월합계 기본 + 일자별 선택 (결정 Q-C)

| 테이블 | v2.0 확정 컬럼 | 비고 |
|--------|---------------|------|
| **order_records (신규)** | period_id, item_id, order_qty, `record_date DATE NULL` | 주문 관리 — 선택 기능(Q-B). 미입력 테넌트는 화면·보고서 숨김. Back Log·자재소요는 파생 뷰(제9장) |
| **sales_records** | qty, amount, `avg_price(파생=amount÷qty)`, partner_id NULL, record_date NULL | 원본 sa 계승 — 수량+매출액 입력, 평균단가 자동(E3). 지역 절단면과 합계 대사(V6) |
| **purchase_records** | item_id, qty, amount, record_date NULL | 월 다회차 허용(원본 pu 10회차 — 행 복수로 자연 수용), 월 가중평균은 엔진 집계 |
| **production_records** | item_id, qty, production_method_id, record_date NULL, **machine_hours NUMERIC(18,2) NULL** | **기계시간 신규(결정 Q-A)** — overhead_alloc_basis='machine_hours'인 테넌트만 입력 필드 노출(E4), 그 외 NULL |

### E6~E9. 노무·경비·조업도·지역 (v1.0 유지 + 변경 1건)

| 테이블 | 내용 |
|--------|------|
| **labor_records** | entry_mode(individual/summary — summary가 엑셀 labor2 직무그룹 6종 계승), pay_type(월급/일급), welfare_cost, overtime_hours, headcount(FTE 소수 허용 — 일용직 환산 3.2명) |
| **labor_allocations** | 제품×공정 현장 인원·시간 (operation2 재현) |
| **expense_records** | 계정별 금액. **v2.0 변경: `alloc_basis_override` 컬럼 폐지** — 배부기준은 테넌트 설정 단일, 기중 변경 금지 [A5·A7] |
| **work_calendars** | 조업도(operation·hr 재현): 카렌다−공휴일−임의공휴일−유지보수=실근무일, 총작업가능시간·생산요구시간·차이시간, 이중 임률 산출 원천. UNIQUE(tenant, period). 일용직 FTE 환산 입력(총인원·총시간·총임금→환산인원·환산임금) |
| **sales_regions / regional_sales** | 판매지역 선택 입력(sales4·obj 재현), 합계 불일치 경고(V6) |

**v2.0 폐지: budgets 테이블** — 계정·인건비그룹 예산 기능은 `period_type='budget'` 가상 기간의 expense_records·labor_records가 완전 대체(이중 구조 제거). 원본 exp2(실적 vs 예산 병렬)는 두 기간의 조인 뷰로 재현.

---

# 7. 도메인 F·G. 재고 원장·원가계산 (9)

### F. 재고 (3) — v1.0 유지

| 테이블 | 핵심 |
|--------|------|
| **inventory_ledger** | append-only, UPDATE/DELETE 금지, 정정=역분개 [A8]. 잔액=SUM(direction×qty) |
| **inventory_adjustments** | 실사 조정 — 사유 필수, 승인 후 원장 기록 |
| **inventory_balances** | 월 스냅샷: 기초+입고−출고=기말(원장 일치 강제), **월총평균단가** [A3]. 제품 재고는 manufacturing_cost로만 평가 [A2] |

### G. 원가계산 (6) — v2.0 변경 집중 구역

### G1. costing_settings (변경)

| 컬럼 | 타입/제약 | 설명 |
|------|----------|------|
| **overhead_alloc_basis** | TEXT NOT NULL CHECK (IN ('direct_labor_cost','direct_labor_hours','machine_hours')) | **제조경비 배부기준 3종 택1 (결정 Q-A — v1.0의 생산수량/노무시간/재료비 3종을 대체)** |
| **alloc_population** | TEXT NOT NULL DEFAULT 'production' CHECK (alloc_population = 'production') | **생산기준 고정 (결정 Q-F)** — 단일값 CHECK로 매출기준 진입 자체를 차단 [A4] |
| effective_fiscal_year | INT | 배부기준 변경은 차기 회계연도 발효(전진법 [A7]) |
| logic_mode | excel_compat / corrected | 유지 (Q16-C) |
| income_tax_rate | NUMERIC(5,2) | 유지 |

### G2. costing_runs / G3. product_costs / G4. cost_allocations

| 테이블 | v2.0 확정 |
|--------|-----------|
| **costing_runs** | 실행 이력, prerequisite(부문분할 완료) 검증, 요약 JSONB — 두 임률(시간당/회사부담) 스냅샷 보존 |
| **product_costs** | **2계층 [A2]**: material_cost + direct_labor_cost + overhead_alloc = `manufacturing_cost`(재고·명세서용) / +admin_labor_alloc(직접노무비 비례)+sga_alloc(매출액 비례) = `full_cost`(관리 뷰) + gross_profit·operating_profit. 유통품은 노무·공수 0 |
| **cost_allocations** | 계정별 기준값·비율·배부액 — SUM(배부액)=경비총액 트랜잭션 검증, 불일치 롤백 [A6]. 기준값 원천: 노무원가→product_costs.direct_labor_cost / 노무시간→공수×수량 / 기계시간→production_records.machine_hours |

### G5. pl_forecast_params — 차월 추정 파라미터 (유지)
차입금·연이자율·매출상승률·인건비상승률·세율 (원본 pl3 그린셀 5종). 변동비 매출 연동·고정비 유지(cost_behavior 활용).

### G6. reconciliation_results (신규) — check 시트의 시스템 승격

| 컬럼 | 타입 | 설명 |
|------|------|------|
| period_id / run_id | UUID NOT NULL | 계산 실행별 산출 |
| qty_diff_material | NUMERIC(18,4) | ① 생산·매출 수량차 재료비 |
| alloc_diff_labor_overhead | NUMERIC(18,4) | ② 노무비+제조경비 배분차 |
| avg_price_diff | NUMERIC(18,4) | ③ 총평균단가차 |
| inventory_adjustment | NUMERIC(18,4) | ④ 재고조정 = ①+②+③ 합산 검증(항등식) |
| theoretical_closing_value / ledger_closing_value | NUMERIC(18,4) | 이론재고 vs 수불부재고 |
| **pl_adjustment_amount** | NUMERIC(18,4) | 손익계산서 **'제품 재고 조정' 라인** 산출값 [A4] |
| adjustment_policy | TEXT CHECK (IN ('apply_monthly','ignore','apply_yearend')) | 원본 권고("무시하거나 연말 1회") 옵션화 |
| check_status | TEXT CHECK (IN ('ok','mismatch')) | OK/불일치 판정 (원본 check 계승) |

검증 리포트(보고서 14)와 손익 재고조정 라인의 단일 원천.

---

# 8. 도메인 H. 검증·AI·가져오기 (7)

validation_warnings, ai_insights(module: costing/abc), uploaded_documents, ai_extractions, import_jobs, import_mapping_templates, notification_outbox — v1.0 유지.

- validation_warnings.severity: warning(저장 허용) / blocking(마감 차단) [A11]
- V1~V8 검증 항목 매핑: V1·V4→G6/트랜잭션, V2·V3→F, V5→work_calendars, V6→regional_sales, V7→ABC 트랜잭션, V8→CI 테스트(엑셀 1원 대조)
- ai_extractions: "AI는 초안, 확정은 사람" — pending_review→approved 승인 파이프라인

---

# 9. 도메인 O. 주문 파생 뷰 (테이블 아님 — 3개)

| 뷰 | 정의 | 원본 |
|----|------|------|
| **v_order_backlog** | 품목별 누적주문(order_records 전기간 합) − 누적생산(production_records 합) = 주문잔량 | orderbal |
| **v_order_material_requirements** | BOM 스냅샷 × 주문수량 전개 + 월총평균단가 → 주문품 자재 총소요(구매계획) | rematerials |
| **v_production_material_requirements** | BOM 스냅샷 × 생산수량 전개 → 생산품 자재 총소요 | pmaterials |

파생 뷰 원칙: 저장 없이 항상 원천에서 도출 — 이중 진실 방지 [A8]. 주문 미사용 테넌트는 앞 2개 뷰 비노출(E4).

---

# 10. 도메인 I~L. ABC 엔진 (16)

### I. 사업부문 (3) — v1.0 유지
business_segments(effective_from 전진법), segment_revenues(기타 부문 매출=카브아웃 원천), segment_allocations(basis_used CHECK 2종 [A10], 합계=원금액 롤백 [A6], 부문귀속명세서 원천).

### J. ABC 기초설정 (7) — v2.0 재편 2건 포함

| 테이블 | v2.0 내용 |
|--------|-----------|
| **abc_settings** | method_mode(classic/tdabc), use_direct_materials 토글, segment_alloc_basis, capacity_default_rate(80.00), **pool_uniform_apply BOOLEAN**(원가풀 일괄적용 Y/N — 원본 4 resource pool 토글) + uniform 시 공통 3기준 비율 컬럼 |
| **activity_templates** | 업종별 표준 활동 시드(전역) — v1.0 유지 |
| **activities** | 활동 마스터(≤15 소프트 경고), department_id(CCR 연결), origin(template/ai_draft/manual), method_override(2차 예비) |
| **pool_basis_ratios (재편 신규)** | **계정별 원가풀 3기준 배부**: account_id, facility_ratio + revenue_ratio + headcount_ratio, CHECK 3비율 합=1. 일괄적용 ON 시 행 생략(설정값 사용). — 원본 '4 resource pool' 정밀 재현 |
| **activity_basis_shares (재편 신규)** | **활동별 3기준 수취 매트릭스**: activity_id, facility_share·revenue_share·headcount_share — **열별(기준별) SUM=1 시스템 강제**(원본 '5 cost activity' 상단 매트릭스). 활동 배부액 = Σ계정[금액×기준비율×활동share] |
| **activity_time_standards** | TDABC 건당 표준 분(minutes_per_unit), effective_from 전진법. **classic 모드에서도 선택 입력 → 간접인건비 시간 검증에 사용** |
| **practical_capacities** | 부서별 실제적 조업능력(이론분×80% 기본), 정밀 마법사=work_calendars 로직 재사용 |

> v1.0의 resource_pools(name+account_ids)·pool_activity_assignments(풀→활동 단일 비율)는 원본 엑셀의 실제 구조(계정→3기준→활동 2단 매트릭스)와 달랐음이 시트 원문 학습으로 확인되어 **폐지·재편**한다.

### K. 원가동인·실적 (2) — v2.0 변경 1건

| 테이블 | v2.0 내용 |
|--------|-----------|
| **activity_drivers** | driver_name·unit, target_scope(1차 service_item 고정), **input_mode TEXT CHECK (IN ('count','percent'))** — 동인 실적을 건수로 받을지 비율(%)로 받을지 토글(원본 '6 activity drivers' 선택 계승). percent 모드는 '활동 % 직접배분' 우회 옵션의 구현체 |
| **driver_actuals** | period·driver·cost_object별 actual_value, **is_estimated 배지**, source(manual/excel/ai_extract). percent 모드 시 SUM=100% 검증 |

### L. ABC 계산·결과 (4) — v1.0 유지 + summary 확장

abc_runs(선행검증 prerequisite_check, **summary JSONB에 간접인건비 시간 검증 결과 포함**: 급여기준 월작업시간 vs 동인총시간 차이 — 원본 생산성 진단), abc_activity_costs(동인단가), abc_object_costs(2계층: direct+abc_overhead, traditional 비교 시뮬레이션 컬럼, has_estimated_driver), abc_unused_capacity(used+unused=practical 항등식 [A9]).

---

# 11. v1.0 → v2.0 변경 대장 (PRD §16 신규 반영 7건 매핑)

| # | PRD 반영사항 | ERD 구현 |
|---|-------------|----------|
| 1 | 기계시간 입력 필드 | production_records.machine_hours (배부기준 ③ 테넌트만 노출) |
| 2 | 예산 시나리오(가상 기간) | fiscal_periods.period_type='budget' + UNIQUE 확장 + budgets 테이블 폐지(흡수) |
| 3 | 주문 잔량·자재소요 | order_records(신규) + 파생 뷰 3개(제9장) |
| 4 | 일자별 선택 모드 확정 | order/sales/purchase/production_records.record_date NULL 패턴 통일 |
| 5 | 생산기준 고정+재고조정 자동화 | costing_settings.alloc_population 단일값 CHECK + reconciliation_results(신규, 4요소 분해·pl_adjustment_amount) |
| 6 | 배부기준 3종 교체 | costing_settings.overhead_alloc_basis CHECK ('direct_labor_cost','direct_labor_hours','machine_hours') + expense_records.alloc_basis_override 폐지 |
| 7 | ABC 파일 발견분 | pool_basis_ratios·activity_basis_shares 재편(3기준 2단 매트릭스), activity_drivers.input_mode 토글, abc_runs.summary 간접인건비 시간 검증, abc_settings.pool_uniform_apply |

기타 정합화: budgets 폐지(이중 진실 제거), v1.0 총괄표 계수 오류 수정, 확장 5건(tenants·items·expense_accounts·fiscal_periods·ai_insights)의 본선 편입.

---

# 12. 공통 설계 규약 (v1.0 전면 상속)

- 금액 NUMERIC(18,4) / 수량 NUMERIC(18,6) / TIMESTAMPTZ UTC — 부동소수점 금지
- 공통 컬럼: id UUID PK, tenant_id FK(전역 테이블 제외), created_at, updated_at
- 출처 필드: source CHECK ('manual','excel','ai_extract','integration')
- RLS 표준 정책(테넌트 격리 + 운영자 SELECT 전용) 전 테넌트 테이블 적용
- 마감잠금 트리거: 월별 데이터 테이블 공통, period_type='actual' AND status='closed' 시 INSERT/UPDATE/DELETE 거부
- 라운딩: 원 단위 끝수는 배부 최종 행에서 조정 [A6]

---

# 13. 테이블 총괄표 (66)

| 도메인 | 테이블 | 수 |
|--------|--------|----|
| A. 테넌트·보안 | tenants, users, login_notification_recipients, login_events, proxy_access_consents, audit_logs, announcements | 7 |
| B. 구독 | subscriptions, cancellation_requests | 2 |
| C. 기초정보 | items, units, item_unit_conversions, partners, departments, processes, expense_accounts, exchange_rates | 8 |
| D. BOM·공정 | bom_lines, bom_snapshots, product_processes, process_snapshots, production_methods, method_process_shares | 6 |
| E. 기간·월데이터 | fiscal_periods, order_records, sales_records, purchase_records, production_records, labor_records, labor_allocations, expense_records, work_calendars, sales_regions, regional_sales | 11 |
| F. 재고 | inventory_ledger, inventory_adjustments, inventory_balances | 3 |
| G. 원가계산 | costing_settings, costing_runs, product_costs, cost_allocations, pl_forecast_params, reconciliation_results | 6 |
| H. 검증·AI·가져오기 | validation_warnings, ai_insights, uploaded_documents, ai_extractions, import_jobs, import_mapping_templates, notification_outbox | 7 |
| I. 사업부문 | business_segments, segment_revenues, segment_allocations | 3 |
| J. ABC 설정 | abc_settings, activity_templates, activities, pool_basis_ratios, activity_basis_shares, activity_time_standards, practical_capacities | 7 |
| K. 동인 | activity_drivers, driver_actuals | 2 |
| L. ABC 결과 | abc_runs, abc_activity_costs, abc_object_costs, abc_unused_capacity | 4 |
| **합계** | | **66** |
| (파생 뷰) | v_order_backlog, v_order_material_requirements, v_production_material_requirements | +3 |

---

# 14. 다음 단계

1. **통합 DDL 마이그레이션 스크립트** — 66 테이블 CREATE + 제약·트리거·RLS + 뷰 3개
2. **엔진 산식 명세서** — 엑셀 셀 → Python 함수 매핑, V8 1원 대조 테스트 케이스(창원산업 2월 실데이터 기준)
3. **화면 정의서(HTML 목업)** + 디자인 가이드
4. 개발 착수 (Claude Code)

— 문서 끝 —
비즈업(Biz-Up) 통합 ERD v2.0 · 2026-07-12 · 페어: 통합 PRD v2.0
