# Genre Profiles

**Phase 4 genre profiles (2026-04-17)**: 장르별 기본값 프리셋.

## 목적

이 템플릿은 기본적으로 **무협(wuxia) 전제**가 많이 박혀 있다 — 한자 MCP 파이프라인, pre-modern 수사 규칙, 객잔/하인 슬롯 등. 현대 로판/헌터물/게임판타지에서는 불필요하거나 노이즈가 된다.

Profile은 **CLAUDE.md의 기본값을 장르에 맞게 선 조정**하기 위한 프리셋이다. INIT-PROMPT가 profile을 선택하면 해당 profile의 값들이 CLAUDE.md §1 / settings/04-worldbuilding.md / settings/01-style-guide.md의 장르 민감 영역에 반영된다.

## 사용법

1. `CLAUDE.md §1`의 `profile:` 필드에 profile 이름 설정 (예: `profile: modern`).
2. 해당 profile 파일을 참고하여 CLAUDE.md / settings 값을 조정.
3. INIT-PROMPT 또는 MIGRATION-PROMPT 사용 시 profile을 인자로 전달하면 자동 적용.

## 현재 지원 Profile

| Profile | 설명 | Hanja | 수사 체계 | 대화 위계 |
|---------|------|-------|----------|----------|
| `wuxia` | 무협/사파/정파 전통 무협 (현재 기본값) | ON | 한글 수사 강제 | 엄격 (사부/문파/형님) |
| `modern` | 현대 일반/직장/오피스 | OFF | 아라비아 OK | 표준 경어 |
| `game-fantasy` | 게임 판타지, 헌터, 시스템물 | OFF | 아라비아 필수 (스탯) | 유연 (플레이어/NPC) |
| `regression` | 회귀/환생/빙의 (장르 무관) | 선택 | POV 시대에 따라 | POV 원래 시대 기준 |
| `romance` | 현대 로맨스/사내/학원 | OFF | 아라비아 OK | 감정/관계 중심 완화 |

## Profile 적용 원칙

- **Profile은 기본값일 뿐, override 가능**. 프로젝트별 CLAUDE.md에서 개별 필드 덮어쓰기 자유.
- **복수 profile**은 권장 안 됨. 복합 장르(예: 무협×로맨스)는 wuxia를 선택한 뒤 romance 요소를 CLAUDE.md §1.2 Thematic Statement에 명시.
- **regression profile**은 "회귀 여부"만 다루고 시대/장르는 추가 설정 필요. 예: `profile: regression` + `settings/04-worldbuilding.md`의 era를 pre-modern으로 설정 = 무협 회귀.

## Phase 4 현재 상태

- ✅ Profile 파일 5종 작성
- ✅ CLAUDE.md §1에 `profile:` 필드 추가
- ⏳ **compile_brief.py의 profile 분기 로직은 후속 작업**: 현재 compile_brief는 `settings/04-worldbuilding.md`에서 era를 추출하므로 profile과 별개로 동작. profile-aware 분기는 Phase 4.1 또는 Phase 5 drift 자동화와 함께 구현.

향후 개선 여지는 `docs/updates/phase-4-genre-profiles.md` "Known Issues / Follow-ups" 참조.
