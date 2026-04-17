# Profile: Regression (회귀 / 환생 / 빙의)

**Status**: 시대 전제와 **무관**하게 "주인공이 미래/전생의 기억을 가진다"를 공통 축으로 삼는 장르.

## 적용 범위

- 회귀 (같은 사람, 과거 시점으로 돌아감)
- 환생 (죽었다가 다른 몸/시대로 태어남)
- 빙의 (소설/게임/역사 속 인물에 들어감)

## ⚠️ 병용 Profile

**regression 단독으로는 불완전하다.** 시대/세계관은 base profile과 **병용**해야 한다.

### `profile:` 필드 syntax (Phase 7 명확화, 2026-04-17)

`CLAUDE.md §1`의 `profile:` 필드에 `regression+{base}` 형태로 표기:

| CLAUDE.md §1 `profile:` 값 | 목표 장르 |
|---------------------------|---------|
| `regression+wuxia` | 무협 회귀/환생 |
| `regression+modern` | 현대 회귀 |
| `regression+game-fantasy` | 헌터/게임판타지 회귀·빙의 |
| `regression+romance` | 로맨스 회귀/환생 |

**적용 순서**: base profile(wuxia/modern/game-fantasy/romance) 전체 적용 → regression.md "Override 규칙"을 그 위에 얹음. §5.1A seed는 **양쪽 seed 병합** (중복 시 regression 우선).

상세 병용 UX: `settings/profiles/README.md § Profile 적용 원칙 > 병용 Profile 적용 순서`.

## Override 규칙 (모든 병용 profile에 공통 적용)

| 필드 | 값 | 근거 |
|------|-----|-----|
| POV 내면 독백 어휘 | **시점 인물의 원래 시대 기준** | pre-modern 배경이라도 회귀자가 현대인이면 내면은 현대 어휘 허용 |
| 외래어 금지 (pre-modern) | **POV 내면 예외** | "에너지, 시스템, 알고리즘" 등 현대 개념어 허용 |
| 아라비아 숫자 금지 (pre-modern) | **POV 내면 예외** | 현대적 수치 판단 자연 |
| 대화 위계 | **외적으로는 현재 시대 기준, 내면은 원래 시대 기준** | 무협 배경 회귀자는 겉으로는 무협식 존대, 내면은 현대 판단 |
| knowledge-map "미래 정보" 축 | **필수 추가** | 회귀자가 알지만 남들이 모르는 사실 추적 |

## 회귀물 특화 트래킹 (summaries/)

- `summaries/knowledge-map.md`에 "회귀 이전 정보" vs "현재 시점 정보" 이원 관리
- `summaries/relationship-log.md`에 "회귀 전 관계" vs "회귀 후 관계" 병기
- `summaries/promise-tracker.md`에 "회귀자가 알지만 아직 안 한 조치" 우선순위 높음

## 톤 기본값

- 기본은 병용 profile의 톤 (wuxia/modern/etc.)
- **추가 톤**: 회귀 냉소, 기시감, "이번에는 다르다" 결의 — 주인공 POV에서 지속적으로 드러나야 함
- **회귀 후 첫 몇 화**: 정보 과잉 투하 위험 주의 (CLAUDE.md §5.2 guardrail G3 참고)

## §5.1A Intentional Style Deviations — regression seed

> INIT-PROMPT 3단계 0번에서 이 seed를 `CLAUDE.md §5.1A` 표에 복사한다. base profile(wuxia/modern 등)의 seed와 **함께** 추가한다 (병합).

| 항목 | 적용 범위 | 허용 변화 | 서사적 이유 |
|------|----------|----------|-----------|
| POV 내면 현대 어휘 (base 시대와 무관) | 주인공 내면 독백 | 회귀자가 전생에 썼던 현대 어휘 자유 사용 | 회귀물 기본 장치. 말과 생각의 괴리 |
| 기시감·예지 선언 | 회귀 이점 시전 장면 | "이번에는 다르다", "그때 그랬지" 등 자기참조 반복 | 장르 시그니처 독백 |
| 감정 진정 대신 냉소 | 초반 5~10화 특히 | 충격/비극 장면에서 감정 대신 계산·냉소 우선 | 회귀자 내면 보호 장치 |

## Writer 힌트

- 주인공 대사: 외적으로 현재 시대 기준 register, 내면은 현대 판단/어휘 허용
- 회귀 트라우마 관리: "미래 기억"이 방아쇠가 되는 장면은 감정 장면으로 밀어야. 단순 정보 덤프 금지 (narrative-fixer S1).
- POV 이외 인물: 회귀 사실을 모름. 그들이 "왜 주인공이 저렇게 행동하지?" 반응을 놓치지 말 것.

## Reviewer 힌트

- POV 현대 어휘는 **주인공 POV 내면/독백에서만** 예외. 서술자 서술이나 외부 관찰 시점에서는 해당 profile의 시대 규칙 적용.
- 정보 격차 체크: 주인공이 미래 정보를 알고 행동하는 장면에서 조연들이 "이상한데"라고 반응하지 않는가? → `/oag-check` 보조.
- 회귀 파괴: 주인공이 회귀 이점을 너무 쉽게 쓰면 초반 5화 내 텐션 붕괴. 첫 아크는 "회귀 사실을 숨기면서 움직이는" 제약을 기본값으로 권장.

## 장르 특화 주의

- **원점 회귀 timeline**: 어느 시점으로 돌아갔는지 `settings/05-continuity.md`에 절대 기준 시점 명시.
- **나비 효과 관리**: 회귀자가 사건 A를 바꾸면 B가 어떻게 달라지는지 `plot/foreshadowing.md`에 분기 표.
- **시간 여행 일관성**: "단일 세계선 vs 병행 세계" 규칙을 CLAUDE.md §5.1 Intentional Mysteries에 등록 (또는 §1 Core Promises에 명시).
