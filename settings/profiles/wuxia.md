# Profile: Wuxia (무협)

**Status**: 현재 템플릿 기본값. `profile: wuxia`는 명시하지 않아도 이 설정이 적용됨.

## 적용 범위

- 정파/사파/낭인 무협, 선협, 선협+회귀 (회귀 요소는 `profile: regression` 고려)
- 전근대 중국/한국/일본 가상 배경
- 무공, 내공, 절기, 비급이 서사 축

## 기본값

| 필드 | 값 | 근거 |
|------|-----|-----|
| `settings/04-worldbuilding.md` era | pre-modern / 무협 | 시대 표기 규칙 자동 ON |
| Hanja pipeline (`novel-hanja` MCP) | ON 권장 | 무공명/지명/인물명 한자 병기 자연 |
| 한글 수사 (pre-modern numeral rules) | 강제 | `1화 → 일 화`, `3일 → 사흘` 등 |
| 아라비아 숫자 | 금지 (in-world 문서 제외) | CLAUDE.md §3.2.11~12 준수 |
| 외래어 | 금지 (회귀 POV 내면 독백 예외) | |
| 대화 위계 | 엄격 | 사부/문파/형님/사제 체계 |
| 기본 조연 슬롯 | 객잔 점원, 숙소 주인, 동행 무사, 제자, 심부름꾼 | `settings/03-characters.md §생활 조연 슬롯` |

## 톤 기본값 (§1.2 Thematic Statement 작성 시 참고)

- 진지/비장 5 : 유머/생활 3 : 전투 2 (조정 가능)
- 정파 주인공: 무겁고 강직한 내면, 공적 존대
- 사파 주인공: 냉소와 자기 보호, 사적 반말과 공적 존대의 이중 전환

## 권장 Settings

- `settings/02-episode-structure.md`: 4500~6000자 (무협 웹소설 표준)
- `settings/07-periodic.md`: Core만 활성화, Specialist는 아크 경계에만
- `settings/01-style-guide.md §0.5 허용 이탈 유형`: 전투/위기/관계 정점에서 단문 급증 허용

## 장르 특화 주의

- 무공 체계 일관성: `summaries/hanja-glossary.md`에 무공명/절기명 등록 필수.
- 세력 관계: `summaries/knowledge-map.md`의 정보 카테고리에 "세력 동향" 추가 권장.
- 내공 수치: 정량적 표기 금지 (`갑자(甲子)` 단위 허용, 숫자 금지).

## Writer/Reviewer 힌트

- Writer: 전통적 "~라 하였다" 계열의 정중 서술 허용, 단 기본 보이스는 현대 한국어 기반 유지.
- Reviewer: "외래어 1개 발견" 플래그는 높은 우선순위. 단 회귀/환생 POV의 내면 독백은 예외 (pov-era-checker 규칙).
