# Hybrid Novel MCP Ideas

> 대상: `claude-codex-novel-templates-hybrid`
>
> 목적: Claude orchestrator + Codex writer 구조에서, 소설 품질을 실질적으로 끌어올리는 추가 MCP 아이디어를 정리한다.
>
> 전제: MCP는 "재미를 대신 판단하는 비평가"보다 "증거를 수집하고 구조화하는 관측기"로 설계하는 편이 안정적이다.

---

## 1. 설계 원칙

### 1.1 무엇을 MCP로 만들 것인가

MCP가 특히 잘하는 일:

- 긴 텍스트에서 반복 패턴을 찾기
- 여러 파일의 정보를 묶어 추적하기
- 사람이나 모델이 놓치기 쉬운 기계적 불일치를 빠르게 찾기
- 리뷰어가 판단하기 전에 "판단 근거"를 모아주기

MCP가 잘 못하는 일:

- "이 장면이 감동적인가?"
- "이 소설이 진짜 재밌는가?"
- "이 문체가 더 좋다/나쁘다"

따라서 좋은 MCP는 대체로 이런 형태를 가진다:

- 텍스트를 읽는다
- 구조화된 후보를 뽑는다
- 근거를 붙인다
- 사람이 최종 판단한다

### 1.2 이 템플릿과의 궁합 기준

좋은 추가 MCP는 아래 셋 중 하나를 강화해야 한다:

1. Codex가 잘 쓰더라도 장기 연재에서 무너지는 지점을 잡는다
2. Claude 리뷰어가 주관적으로 과잉 교정하지 않도록 증거를 준다
3. `summaries/`, `plot/`, `review-log`를 실제 운영 데이터베이스처럼 만든다

### 1.3 우선순위 판단 기준

- 연재 길이가 길수록 가치가 커지는가
- 기존 checker와 겹치지 않고 빈 구간을 메우는가
- 출력이 fix-spec이나 review-log로 자연스럽게 연결되는가
- 오탐이 나더라도 소설을 평평하게 만들 위험이 낮은가

---

## 2. 추천 순위

### 최우선 추천

1. `voice-drift-mcp`
2. `event-causality-mcp`
3. `promise-debt-mcp`
4. `term-onboarding-mcp`

### 2차 추천

5. `relationship-tension-mcp`
6. `hook-pattern-mcp`
7. `naming-variant-mcp`
8. `scene-util-mcp`

### 선택적 고급 도구

9. `theme-drift-mcp`
10. `sensory-pattern-mcp`

---

## 3. MCP 상세 설계

## 3.1 `voice-drift-mcp`

### 한 줄 설명

캐릭터별 대표 대사와 최근 실제 대사를 비교해, 말투와 보이스 드리프트를 증거 기반으로 잡는 도구.

### 왜 필요한가

현재 템플릿은 `settings/03-characters.md`의 대표 대사와 `unified-reviewer`의 말투 검사를 가지고 있다. 하지만 장기 연재에서는 리뷰어가 "왠지 다르다" 수준으로 느끼는 경우가 많고, 그 판단이 주관화되기 쉽다.

이 도구는 다음을 구조화해 준다:

- 존댓말/반말 전환
- 어미 습관 변화
- 문장 길이 변화
- 특유 어휘 소실
- 과도한 평균화

### 입력

- `settings/03-characters.md`
- `chapters/**/*.md`
- 선택적으로 `summaries/character-tracker.md`

### 핵심 추출 단위

- 캐릭터 대표 대사
- 최근 N화의 실제 대사 샘플
- 화자 식별 가능한 대사만 추출

### 출력

예시:

```markdown
# Voice Drift Report

## {{캐릭터명}}

- baseline:
  - 존대/반말: 반말
  - 종결 패턴: "~냐", "~지", 짧은 단문
  - 특징 어휘: "웃기지 마", "됐어", "알아서"

- recent sample window: 21~30화

### drift candidates

1. 말투 격식 상승
   - 근거 화수: 24, 27, 29
   - 관측: 평소 반말 중심인데 "그렇습니까", "알겠습니다" 사용
   - 판단: 관계 변화나 위장 상황 없으면 drift 가능성 높음

2. 문장 길이 평균 상승
   - baseline: 짧은 단문
   - recent: 설명형 장문 증가
   - 판단: 보이스 평탄화 가능성
```

### 배치 위치

- 매 5화 periodic check
- 새 핵심 인물 등장 후 3~5화 뒤
- 아크 경계의 `pov-era-check`와 별개 축으로 실행 가능

### fix 연결

- 자동 수정 금지
- `unified-reviewer`의 B1, B2 보조 증거
- 필요시 `narrative-fix`의 보이스 보존 제약 강화

### 장점

- 리뷰어의 취향 개입을 줄인다
- 캐릭터 개성 붕괴를 조기 탐지한다
- 대화가 "평균체"로 수렴하는 걸 늦춘다

### 리스크

- 감정 변화나 사회적 상황에 따른 일시적 말투 변화도 drift로 오탐할 수 있다

### 오탐 방지 규칙

- 단발성은 경고하지 않는다
- 최소 3회 이상 또는 3화 이상 누적 패턴만 후보화
- 관계/위장/공적 자리 같은 상황 태그를 있으면 예외 처리

### MVP 범위

- 존대/반말
- 대표 어미
- 대표 어휘
- 평균 문장 길이

### 확장 범위

- 캐릭터별 금기어
- 웃음/침묵/회피 대사 패턴
- 호칭 변화 감지

---

## 3.2 `event-causality-mcp`

### 한 줄 설명

화별 핵심 사건을 `원인 → 행동 → 결과 → 후폭풍` 체인으로 추출해 인과가 끊긴 지점을 찾는 도구.

### 왜 필요한가

현재 `why-check`는 설명 누락, `oag-check`는 행동 누락, `scene-logic-check`는 장면 물리를 본다. 그런데 독자 체감상 가장 자주 문제 되는 건 이 셋의 중간 지대다.

예:

- 사건은 일어났는데 왜 이 방향으로 번졌는지 약함
- 행동은 했는데 결과가 장면 밖으로 사라짐
- 큰 변화가 있었는데 후폭풍이 실종

이 도구는 "원인과 결과의 사슬"을 구조화해 준다.

### 입력

- `chapters/**/*.md`
- 선택적으로 `summaries/episode-log.md`

### 출력

```markdown
# Event Causality Report

## 17화

### 사건 C-017-02
- 원인: 주인공이 밀서를 확보함
- 행동: 추적을 피하기 위해 즉시 은신처로 이동
- 직접 결과: 적 세력이 밀서 분실을 인지
- 기대 후폭풍: 추적 강화, 동맹 의심, 내부 색출

판정:
- 직접 결과: 본문 존재
- 후폭풍: 18~20화에서 부재
- 상태: CONSEQUENCE GAP 후보
```

### 배치 위치

- 아크 경계의 `why-check` 직전 또는 직후
- 중형 아크의 중간 점검

### fix 연결

- 설명 누락이면 `why-check` 쪽
- 행동 미비면 `oag-check` 쪽
- 후폭풍 실종이면 `review-log`의 HOLD 또는 `narrative-fix --source why-check`

### 장점

- `why`와 `oag` 사이의 빈 구간을 메운다
- 아크 통독 전에 구조적 냄새를 먼저 잡는다
- "사건은 많지만 기억에 안 남는 소설" 문제를 줄인다

### 리스크

- 사건 추출이 과도하면 보고서가 비대해진다

### 오탐 방지 규칙

- 사소한 일상 행동은 제외
- 세계 상태나 관계 상태를 바꾸는 사건만 추출
- 최대 사건 수를 화당 3~5개로 제한

### MVP 범위

- 주요 사건 추출
- 직접 결과 유무
- 1~3화 후 후폭풍 유무

### 확장 범위

- arc-level causality map
- 독자 혼란 유발 지점 우선순위화

---

## 3.3 `promise-debt-mcp`

### 한 줄 설명

복선, 약속, 유예된 설명, HOLD 항목을 묶어서 "지금 무엇을 언제까지 갚아야 하는가"를 추적하는 도구.

### 왜 필요한가

장기 연재는 보통 "구멍"보다 "빚" 때문에 무너진다. 독자는 정확히 기억하지 못해도, 약속을 너무 오래 방치하면 체감적으로 신뢰를 잃는다.

현재 템플릿에는 아래 파일들이 흩어져 있다:

- `plot/foreshadowing.md`
- `summaries/promise-tracker.md`
- `summaries/review-log.md`
- `summaries/decision-log.md`
- `running-context.md`

이걸 하나의 빚 장부로 묶어 보는 도구가 있으면 운영이 훨씬 쉬워진다.

### 입력

- `plot/foreshadowing.md`
- `summaries/promise-tracker.md`
- `summaries/review-log.md`
- `summaries/decision-log.md`
- `plot/arc-*.md`

### 출력

```markdown
# Promise Debt Report

## 긴급 상환 필요

1. PD-014
   - 유형: forward-fix
   - 출처: HOLD-004
   - 내용: 주인공이 왜 즉시 복수하지 않았는가에 대한 보상 장면 필요
   - 기한: 23화 이전
   - 상태: overdue risk

2. PD-021
   - 유형: foreshadow
   - 내용: 청목패의 용도 암시
   - 기대 회수 범위: arc-03
   - 상태: 정상
```

### 배치 위치

- 매 화 집필 전 supervisor 체크
- 아크 마감 직전 필수 실행

### fix 연결

- `scope: current-arc` overdue → blocker
- `scope: next-arc` carry-forward 확인
- plot 조정이 필요하면 `plot-surgeon`

### 장점

- 장기 떡밥 방치 방지
- `HOLD` 시스템 실전성 강화
- 다음 아크 설계 때 놓치는 부채 감소

### 리스크

- 모든 복선을 debt로 읽으면 소설이 과도하게 기계적이 된다

### 오탐 방지 규칙

- `의도적 미스터리`는 debt와 분리
- 감정적 여운이나 테마적 열린 결말은 debt로 취급하지 않음
- 기대 회수 범위를 명시한 항목만 강한 debt로 본다

### MVP 범위

- due date 계산
- overdue 경고
- `current-arc` vs `next-arc` 구분

### 확장 범위

- 중요도 점수
- 독자 기억도 추정

---

## 3.4 `term-onboarding-mcp`

### 한 줄 설명

세계관 용어의 첫 등장, 첫 설명, 설명 필요 시점을 추적해 독자 온보딩 실패를 줄이는 도구.

### 왜 필요한가

세계관이 강한 작품은 용어를 "작가만 알고 독자는 모르는 상태"로 너무 오래 끌기 쉽다. 한자 병기와 개념 설명은 다르다. 용어를 읽을 수 있다고 이해한 건 아니다.

이 도구는 특히 아래 장르에 유효하다:

- 무협
- 동양 판타지
- SF
- 정치/조직 중심 장르

### 입력

- `settings/04-worldbuilding.md`
- `summaries/explained-concepts.md` 또는 유사 파일
- `chapters/**/*.md`

### 출력

```markdown
# Term Onboarding Report

## 미설명 위험 용어

1. 혈사문
   - 첫 등장: 6화
   - 현재 상태: 이름만 등장, 기능 설명 없음
   - 위험도: 중간
   - 권장 마감: 8화 전

2. 귀환진
   - 첫 등장: 11화
   - 현재 상태: 사용 장면 있음, 작동 조건 설명 없음
   - 위험도: 높음
```

### 배치 위치

- arc planning 직후
- worldbuilding-heavy 작품의 매 5화 점검

### fix 연결

- `Reader Onboarding` 섹션 업데이트
- `why-check`의 미설명 판정 완화/강화 근거

### 장점

- 세계관 과부하 완화
- 독자 이탈 포인트 감소
- 한자 병기와 설명을 분리해서 관리 가능

### 리스크

- 모든 용어를 빨리 설명하게 유도하면 미스터리감이 죽는다

### 오탐 방지 규칙

- 핵심 이해에 필요한 용어만 추적
- 분위기용 명사는 제외
- `Intentional Mysteries` 등록 항목은 예외

### MVP 범위

- 첫 등장 화수
- 설명 여부
- 설명 필요 기한

### 확장 범위

- 독자 이해 의존도 추정
- 설명 과밀도 경고

---

## 3.5 `relationship-tension-mcp`

### 한 줄 설명

핵심 인물쌍의 갈등, 거리, 접촉 빈도, 최근 사건을 시계열로 정리해 관계 엔진의 열기를 측정하는 도구.

### 왜 필요한가

관계는 자주 "좋은 장면이 있었는지"보다 "붙어야 할 둘이 너무 오래 안 붙는지"에서 무너진다.

### 입력

- `summaries/relationship-log.md`
- `episode-log.md`
- 선택적으로 본문

### 출력

- 인물쌍별 최근 접촉
- 갈등 해결/재점화 여부
- 긴장도 하락 경고

### 유효 장르

- 로맨스
- BL/GL
- 라이벌 중심 장르
- 사제/가문/정파 관계가 중요한 무협

---

## 3.6 `hook-pattern-mcp`

### 한 줄 설명

최근 화들의 오프닝/엔딩 훅 유형을 자동 태깅해 반복과 무력화를 방지하는 도구.

### 왜 필요한가

연재물은 훅이 약해서 망하기도 하지만, 더 자주 같은 훅만 반복해서 무뎌진다.

### 추적 대상

- 오프닝 유형: 전투, 대화, 여운 직후, 설명, 감각, 공백, 회상
- 엔딩 유형: 폭로, 위기, 감정 여운, 결심, 등장, 반전, 미완 행동

### 출력

- 최근 5화 분포
- 동일 유형 3회 연속 경고
- 특정 유형 과다 사용 경고

---

## 3.7 `naming-variant-mcp`

### 한 줄 설명

인명, 지명, 조직명, 무공명, 별호, 호칭 변형을 자동 수집해 canonical form과 비교하는 도구.

### 왜 필요한가

무협/사극/판타지는 오타보다 "비슷하지만 다른 표기"가 더 위험하다.

예:

- 천외귀환 / 천외 귀환
- 남궁세가 / 남궁 가문
- 빙혼검 / 빙혼의 검

### 입력

- `reference/name-table.md`
- `settings/03-characters.md`
- `settings/04-worldbuilding.md`
- `chapters/**/*.md`

### 출력

- 표기 변형 목록
- 권장 canonical form
- 호칭과 본명 혼동 후보

---

## 3.8 `scene-util-mcp`

### 한 줄 설명

각 장면이 실제로 어떤 서사 기능을 수행하는지 태깅해, 기능 없는 장면이나 같은 기능만 반복하는 장면을 찾는 도구.

### 핵심 질문

- 이 장면은 무엇을 전진시켰는가
- 플롯/감정/관계/세계관/훅 중 최소 하나를 수행했는가
- 같은 기능만 3장면 연속 반복되는가

### 장점

- 페이싱 점검에 유용
- "잘 써놨는데 안 남는 화"를 줄인다

### 리스크

- 너무 기계적으로 적용하면 분위기 장면을 과소평가할 수 있음

---

## 3.9 `theme-drift-mcp`

### 한 줄 설명

주제 선언과 최근 화들의 thematic function을 비교해, 주제가 장기간 침묵하는 구간을 찾는 도구.

### 장점

- 장기 연재에서 방향 감각 유지
- plot-functional but thematically empty 에피소드 누적 방지

### 리스크

- 너무 엄격하면 모든 화가 주제를 노골적으로 말하게 될 수 있음

### 사용 권장 방식

- 경고 전용
- 자동 수정 금지
- `narrative-review` 보조 지표로만 사용

---

## 3.10 `sensory-pattern-mcp`

### 한 줄 설명

감각 사용, 신체 반응, 분위기 문장, 환경 클리셰의 반복을 세밀하게 추적하는 도구.

### 잡고 싶은 패턴

- "숨을 삼켰다"
- "손끝이 차가워졌다"
- "침묵이 내려앉았다"
- "형광등이 떨렸다" 같은 환경 플레이스홀더

### 장점

- prose 패턴 개선에 도움
- repetition-checker보다 미세한 레벨 포착 가능

### 리스크

- 서정적 보이스를 기계적으로 잘라낼 위험

### 사용 원칙

- `금지`가 아니라 `관측`
- style lexicon, 시그니처 표현 면책과 함께 써야 함

---

## 4. 구현 우선순위 제안

## Phase 1: 바로 만들 가치가 큰 것

### 1. `promise-debt-mcp`

이유:

- 이미 있는 파일들을 묶는 수준이라 구현 난이도가 낮다
- 운영 체감이 즉시 좋다
- `HOLD` 시스템을 실전적으로 만든다

### 2. `voice-drift-mcp`

이유:

- hybrid 구조에서 Claude 리뷰어의 주관을 줄여 준다
- 캐릭터 개성 붕괴는 장기 연재에서 치명적이다

### 3. `term-onboarding-mcp`

이유:

- 세계관 강한 작품에서 독자 이탈 방지 효과가 크다
- `Reader Onboarding`과 곧바로 연결된다

### 4. `event-causality-mcp`

이유:

- 제일 강력하지만 구현은 더 어렵다
- 제대로 만들면 why/oag 사이의 공백을 크게 줄인다

---

## 5. 권장 출력 형식 원칙

모든 MCP는 가능한 한 아래 원칙을 따르는 편이 좋다.

### 5.1 판정 대신 후보

좋은 형식:

- candidate
- risk
- evidence
- recommended check

나쁜 형식:

- 이 장면은 나쁨
- 이 문체는 별로임
- 이 소설은 재미없음

### 5.2 근거 최소 단위

각 항목은 가능하면 아래를 가져야 한다:

- 대상 화수
- 짧은 인용 또는 anchor
- 참조 파일
- 왜 후보가 되었는지

### 5.3 자동 수정 금지 범위

아래 축은 자동 fix와 직접 연결하지 않는 편이 낫다:

- theme
- style preference
- emotional impact
- literary quality

아래 축은 fix-spec과 연결하기 좋다:

- naming variant
- overdue promise debt
- obvious onboarding gap
- clear voice register drift

---

## 6. 지금 만들지 말아야 할 MCP

## 6.1 재미 점수 MCP

문제:

- 지나치게 주관적이다
- 장르마다 기준이 다르다
- 평균적이고 안전한 방향만 밀게 된다

## 6.2 문체 우열 점수 MCP

문제:

- 보이스 다양성을 해친다
- "표준 한국어"로 과잉 수렴시킬 위험이 크다

## 6.3 감동 판정 MCP

문제:

- 감정은 준비와 맥락의 함수이지 단문 판정의 대상이 아니다
- 오탐 시 가장 해로운 과잉 교정을 유도한다

---

## 7. 추천 로드맵

### 로드맵 A: 운영 안정화 우선

1. `promise-debt-mcp`
2. `naming-variant-mcp`
3. `term-onboarding-mcp`

이 경로는 연재 운영을 덜 불안하게 만든다.

### 로드맵 B: 서사 품질 우선

1. `voice-drift-mcp`
2. `event-causality-mcp`
3. `scene-util-mcp`

이 경로는 "글은 괜찮은데 이야기 힘이 약해지는" 문제를 줄인다.

### 로드맵 C: 무협/판타지 특화

1. `term-onboarding-mcp`
2. `naming-variant-mcp`
3. `promise-debt-mcp`
4. `relationship-tension-mcp`

---

## 8. 최종 권고

이 하이브리드 템플릿에 추가할 MCP는 "더 좋은 문장을 쓰게 만드는 심사관"보다 "무너질 위험을 조기에 관측하는 레이더"여야 한다.

가장 추천하는 첫 구현 세트는 아래 넷이다:

1. `promise-debt-mcp`
2. `voice-drift-mcp`
3. `term-onboarding-mcp`
4. `event-causality-mcp`

이 넷은 각각 다음을 잡는다:

- 약속 방치
- 캐릭터 보이스 평탄화
- 세계관 온보딩 실패
- 인과와 후폭풍의 붕괴

즉, 장기 연재 소설이 AI로 흔히 무너지는 네 축을 비교적 안전하게 커버한다.

