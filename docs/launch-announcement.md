# costmgr 1st release — 출시 안내

**Date:** 2026-08-22
**Status:** GA (General Availability)

---

## 1. 출시 배경

costmgr는 중소규모 제조·유통·서비스·IT 4개 산업군의 ABC/TDABC 원가관리 SaaS입니다.
기존의 스프레드시트 기반 원가 계산은 비효율적이고 휴먼 에러가 많았습니다.
costmgr는 다음 4가지 핵심 가치를 제공합니다.

1. **자동화**: AI 기반 데이터 입력 + 원가 계산
2. **정확성**: ABC + TDABC 결합으로 정확한 원가 산출
3. **실시간성**: LISTEN/NOTIFY 기반 실시간 원가 반영
4. **보안**: 2FA + RLS + AES-256-GCM으로 안전한 데이터 관리

## 2. 핵심 기능

- **ABC 엔진 (TDABC 통합)**: 활동기준원가 + 시간동인 원가배분
- **AI 인사이트**: 비용 절감 후보, 이상 패턴, 예측 자동 생성
- **LISTEN/NOTIFY 실시간**: PostgreSQL NOTIFY 기반 캐시 무효화
- **2FA 보안**: TOTP 기반 2차 인증 (Epic 12 wire 정합)
- **다중 테넌트**: RLS 기반 tenant 격리 (CR 0-2 RLS lesson)
- **4-industry 지원**: 제조 + 제조+유통 + 서비스 + IT

## 3. 타겟 시장

- **manufacturing** (제조): 단일 제조업종
- **manufacturing_service** (제조 + 유통/서비스 겸영)
- **service** (서비스): 서비스업종
- **manufacturing_service_other** (제조 + 유통/서비스 + IT 겸영)

## 4. 향후 로드맵

- **Phase 5** (예정): 다중 리전 백업
- **Epic 16+** (예정): 추가 기능 (TBD)
- **2026 Q4**: 모바일 앱 출시 (예정)
- **2027 Q1**: AI 인사이트 정교화 (예정)

자세한 로드맵은 [master PRD §15 로드맵](../_bmad-output/planning-artifacts/prd.md)을 참조하세요.

---

**Contact:** support@bizup.kr
**Status page:** status.bizup.kr (예정)
