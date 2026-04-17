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
- **복합 장르** (예: 무협×로맨스, 현대 로맨스 회귀)는 아래 규칙을 따른다.

### Profile syntax (Phase 7 명확화, 2026-04-17)

`CLAUDE.md §1 profile:` 필드는 아래 3가지 형태를 허용한다.

| Syntax | 의미 | 예시 |
|--------|------|------|
| 단일 profile | 해당 profile 단독 적용 | `profile: wuxia` |
| **`regression+{base}`** | regression 공통 override + base profile 적용 | `profile: regression+wuxia`, `profile: regression+modern` |
| 혼합 장르 | **단일 profile + §1.2 Thematic Statement 명시** | `profile: wuxia` + Thematic에 "무협 로맨스"로 명시 |

### 병용 Profile 적용 순서

`regression+wuxia`를 예로:

1. **Base profile(wuxia)** 적용: wuxia.md의 "기본값 override 표" + "§5.1A seed" + 조연 슬롯
2. **Regression profile** override 추가: regression.md의 "Override 규칙" 섹션을 base 위에 얹음 (POV 내면 예외, knowledge-map 이원 관리 등)
3. **§5.1A 표**: 두 profile의 seed를 **모두 병합** (중복 항목은 regression 우선)
4. **다른 summaries/ / settings/**: base profile의 설정을 그대로. regression은 override만 추가.

### 혼합 장르 처리

무협 로맨스(무로맨), 현대 판타지 등은 `regression+X`처럼 전용 syntax가 없다. 대신:

- base profile 하나 선택 (예: wuxia 또는 romance 중 하나)
- `CLAUDE.md §1.2 Thematic Statement`에 "혼합 장르" 명시
- `settings/01-style-guide.md §0 Voice Profile` 작성 시 양쪽 장르의 보이스 특징을 합성
- `§5.1A`에는 base profile seed + 필요 시 다른 profile에서 추가 항목을 **수동 복사**

> 복수 profile 동시 적용을 런타임이 자동 지원하지 않는다. Phase 4.1(compile_brief profile 분기)에서 단일 profile 동작부터 구현 예정.

## Phase 4 현재 상태

- ✅ Profile 파일 5종 작성
- ✅ CLAUDE.md §1에 `profile:` 필드 추가
- ⏳ **compile_brief.py의 profile 분기 로직은 후속 작업**: 현재 compile_brief는 `settings/04-worldbuilding.md`에서 era를 추출하므로 profile과 별개로 동작. profile-aware 분기는 Phase 4.1 또는 Phase 5 drift 자동화와 함께 구현.

향후 개선 여지는 `docs/updates/phase-4-genre-profiles.md` "Known Issues / Follow-ups" 참조.
