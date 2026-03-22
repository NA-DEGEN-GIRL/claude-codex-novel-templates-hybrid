# Hybrid Agents Review

> 검토일: 2026-03-23
> 대상: `/root/novel/claude-codex-novel-templates-hybrid/.claude/agents`
> 범위: 에이전트 정의 문서 리뷰만 수행. 실제 end-to-end 실행 검증은 포함하지 않음.

---

## 핵심 판단

전체적으로는 잘 설계된 편이다. 특히 `oag-checker`, `why-checker`, `pov-era-checker`, `repetition-checker`, `book-reviewer`는 역할이 선명하고, AI 소설이 흔히 망가지는 지점을 꽤 정확히 겨냥한다.

다만 **fix 계층과 플롯 수선 계층에는 아직 hybrid 이전의 lean 흔적이 남아 있다.** 가장 큰 문제는 `plot-surgeon`과 `narrative-fixer`가 현재 하이브리드 운영 철학과 완전히 정합적이지 않다는 점이다. 진단 계열은 대체로 강하고, 수정 계열은 일부 재정렬이 필요하다.

---

## Findings

### 1. `plot-surgeon`은 현재 세트에서 가장 위험하다

파일:
- [plot-surgeon.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/plot-surgeon.md#L20)
- [plot-surgeon.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/plot-surgeon.md#L219)
- [plot-surgeon.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/plot-surgeon.md#L383)
- [plot-surgeon.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/plot-surgeon.md#L171)
- [plot-surgeon.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/plot-surgeon.md#L245)

문제:
- 문서 초반에서는 `사용자 승인 필수`라고 선언하지만, 후반에서는 `AUTO-APPROVED` 조건을 두어 승인 없이 적용할 수 있게 한다.
- 외부 AI `ask_gpt`, `ask_gemini` 전제를 아직 품고 있다.
- 본문 수정 handoff가 여전히 `writer`와 `narrative-fixer` 중심이다. 현재 hybrid의 `Codex writer/fixer` 실운영과 바로 맞물리는 정의는 아니다.

판단:
- 이 에이전트는 아이디어 자체는 좋지만, 현재 구조 기준으로는 **REVISE 우선순위 최상**이다.

### 2. `narrative-fixer`는 내용은 좋지만 실행 주체가 stale 하다

파일:
- [narrative-fixer.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/narrative-fixer.md#L11)
- [narrative-fixer.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/narrative-fixer.md#L76)
- [narrative-fixer.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/narrative-fixer.md#L105)
- [narrative-fixer.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/narrative-fixer.md#L482)

문제:
- 본문 수정, 요약 갱신, 리뷰 재실행, 커밋까지 직접 수행하는 lean형 수정자에 가깝다.
- 현재 하이브리드가 `Claude 진단 + Codex 텍스트 수정`으로 기울어 있다면, 이 정의는 런타임 주체가 맞지 않는다.
- `사용자 승인 후 진행` 게이트가 있어 자동화 루프 안에 넣기는 어렵다.

판단:
- 진단을 읽고 어떤 식으로 최소 수정할지에 대한 사고 방식은 아주 좋다.
- 그러나 현재 hybrid에서 그대로 “실행 에이전트”로 보기엔 **역할 정렬이 덜 끝난 상태**다.

### 3. `writer.md`는 deprecated라고 해놓고 주변 에이전트들이 계속 참조한다

파일:
- [writer.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/writer.md#L1)
- [oag-checker.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/oag-checker.md#L224)
- [plot-surgeon.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/plot-surgeon.md#L246)

문제:
- `writer.md`는 더 이상 hybrid에서 쓰지 않는다고 명시돼 있지만, 다른 에이전트 문서에서는 여전히 handoff 대상으로 등장한다.
- 문서 독자 기준으로는 “죽은 에이전트인지, fallback인지, 실제 실행 주체인지”가 완전히 정리돼 있지 않다.

판단:
- 지금 상태는 기능적 결함이라기보다 **문서 경계 문제**다.
- 다만 플롯 수선이나 OAG 후속 수정에서 실제 라우팅 혼선을 만들 수 있다.

### 4. `why-checker`는 OAG 분리를 선언했지만 일부 질문 축이 아직 겹친다

파일:
- [why-checker.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/why-checker.md#L24)
- [why-checker.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/why-checker.md#L56)
- [why-checker.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/why-checker.md#L79)
- [why-checker.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/why-checker.md#L126)

문제:
- 문서상으로는 OAG를 분리했다고 하지만, `명백한 대안 행동을 하지 않았는가`, `이미 가진 정보로 왜 대응하지 않았는가` 같은 질문은 여전히 OAG와 강하게 겹친다.
- 실제 운용 시 WHY와 OAG가 같은 결함을 다른 이름으로 반복 보고할 가능성이 있다.

판단:
- 완전히 잘못된 설계는 아니다.
- 다만 WHY는 설명 공백, OAG는 행동 공백으로 더 날카롭게 분리해 두는 편이 좋다.

### 5. `unified-reviewer`는 매우 강하지만 약간 공격적인 플래그 성향이 있다

파일:
- [unified-reviewer.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/unified-reviewer.md#L7)
- [unified-reviewer.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/unified-reviewer.md#L38)
- [unified-reviewer.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/unified-reviewer.md#L61)

문제:
- 초반 역할 선언은 `When in doubt, flag it` 쪽인데, 뒤에서는 `명백한 위반만`이라는 방어선도 같이 둔다.
- 실제 모델 성향에 따라 false positive가 늘 수도, 반대로 잘 작동할 수도 있는 구조다.

판단:
- 핵심 reviewer로서는 아주 강하다.
- 다만 문체·심리 쪽은 `의심되면 무조건 플래그`보다 `근거 약하면 ⚠️ 또는 보류`로 더 일관되게 정리하면 안정성이 올라간다.

---

## 에이전트별 검토

### 1. `writer.md`

파일:
- [writer.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/writer.md#L1)

평가:
- **DEPRECATED / reference-only**

강점:
- 집필 체크리스트가 매우 촘촘하다.
- 사전 계획, 자기 점검, summary 갱신, 리뷰 연결까지 한 사이클이 명확하다.
- OAG, why, 반복, 훅, theme까지 실제로 소설을 굴리는 데 필요한 감시점이 잘 들어가 있다.

리스크:
- 하이브리드에서 실사용하지 않는 문서인데도 내용이 지나치게 완성형이라, 다른 문서가 여기에 다시 기대기 쉽다.
- 지금은 “참고용”보다 “잠든 주력 문서”처럼 보인다.

총평:
- 내용은 우수하다.
- 하지만 hybrid 기준에선 **남겨 두되, 다른 문서에서 직접 참조하지 않게 끊는 편**이 맞다.

### 2. `unified-reviewer.md`

파일:
- [unified-reviewer.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/unified-reviewer.md#L1)

평가:
- **GO**

강점:
- 연속성, 서사 품질, 교정, 외부 피드백, summary 검증까지 한 번에 묶은 핵심 reviewer다.
- `style consistency`, `AI psychological patterns`, `summary validation`이 특히 실전적이다.
- 매화용 reviewer로 쓰기 좋게 범위를 계층화했다.

리스크:
- 범위가 넓어 모델 컨디션에 따라 피상적으로 읽을 위험이 있다.
- 플래그 성향이 강하면 창작 위축으로 이어질 수 있다.

총평:
- 현재 세트의 중추다.
- 오히려 이 에이전트가 무너지면 전체 품질 관리가 흔들린다.

### 3. `full-audit.md`

파일:
- [full-audit.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/full-audit.md#L1)

평가:
- **GO**

강점:
- 장편 전수감사에 필요한 chunking, carry-forward, integrity check까지 잘 설계돼 있다.
- 기계적 오류와 장기 패턴을 동시에 보는 구조가 좋다.
- `Phase 2.5` 자연스러움 별도 패스는 현실적인 타협이다.

리스크:
- 문서가 길고 무겁다. 실제 실행자는 꼼꼼한 운영자가 아니면 일부 단계를 생략할 가능성이 있다.
- 1M 컨텍스트 전제를 강하게 탄다.

총평:
- 무거운 대신 제대로 만들었다.
- “연재 중 자주”보다 “아크 단위 정비”용으로 가치가 크다.

### 4. `book-reviewer.md`

파일:
- [book-reviewer.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/book-reviewer.md#L1)

평가:
- **GO**

강점:
- 설정과 plot을 보지 않고 본문만 읽는 독자 모드를 강하게 유지한다.
- reader-facing / author-facing 분리가 아주 좋다.
- “수정하지 말고 평가만 하라”는 선이 분명하다.

리스크:
- 실제로는 장편일수록 인용·비교 작품 판단이 모델 편차를 탈 수 있다.

총평:
- 품질이 좋다.
- 특히 `narrative-reviewer`와 함께 쓰면 “개발편집”과 “독자 반응”을 분리해서 볼 수 있다.

### 5. `korean-naturalness.md`

파일:
- [korean-naturalness.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/korean-naturalness.md#L1)

평가:
- **GO**

강점:
- 오탐이 문체를 평탄화할 수 있다는 걸 명시적으로 알고 있다.
- 결합 자연성 검사와 AI 문체 패턴 검출의 균형이 좋다.
- “고정 치환”이 아니라 “수정 방향”만 제시하게 한 점이 좋다.

리스크:
- 운영자가 보수적으로 안 쓰면 문체 교정기가 평균체 제조기로 변할 수 있다.

총평:
- 설계는 좋다.
- 실제 성패는 리뷰어 discipline에 달렸다.

### 6. `oag-checker.md`

파일:
- [oag-checker.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/oag-checker.md#L1)

평가:
- **GO**

강점:
- 이 세트에서 가장 인상적인 에이전트 중 하나다.
- `Generate-Then-Check`, `State Snapshot`, `Binary Verification`이 매우 설득력 있다.
- OAG를 WHY와 분리한 발상도 맞다.
- `patch-feasible / plot-change-needed` 분류는 후속 라우팅 가치가 크다.

리스크:
- 캐릭터 성격 해석이 잘못되면 기대 행동 생성이 틀어질 수 있다.
- 하지만 그 위험을 감안해도 현재 구조에 꼭 필요한 감시다.

총평:
- 유지 가치가 매우 높다.

### 7. `why-checker.md`

파일:
- [why-checker.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/why-checker.md#L1)

평가:
- **GO, but REVISE overlap**

강점:
- text-only constraint가 분명하다.
- 질문 생성 패스와 답변 감사 패스를 분리한 구조가 좋다.
- 독자 입장에서 “작가는 아는데 독자는 모르는” 구멍을 잘 잡게 되어 있다.

리스크:
- OAG와의 경계가 아직 일부 겹친다.
- consequence audit와 action gap이 맞물릴 때 보고서가 중복될 수 있다.

총평:
- 매우 유용하다.
- 다만 질문 카테고리에서 OAG 영역을 더 걷어내면 더 좋아진다.

### 8. `scene-logic-checker.md`

파일:
- [scene-logic-checker.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/scene-logic-checker.md#L1)

평가:
- **GO**

강점:
- 범위가 좁고 선명하다.
- 관습적 생략을 존중하면서도, 제약 조건이 걸린 경우만 엄격하게 보는 판단이 좋다.
- 배치 검사에 적합하게 가볍다.

리스크:
- 아주 문학적인 서술이나 압축적인 액션에서는 모델 판단 차가 생길 수 있다.

총평:
- 좋은 보조 진단기다.

### 9. `pov-era-checker.md`

파일:
- [pov-era-checker.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/pov-era-checker.md#L1)

평가:
- **GO**

강점:
- 시점 지식 누수와 시대 부적합을 한 번에 잡는 방향이 좋다.
- 전근대 배경, 회귀물, 시스템 예외까지 다뤄서 실전성이 높다.
- knowledge-map과 style-lexicon을 함께 보는 점이 유효하다.

리스크:
- knowledge-map 품질이 낮으면 판정도 흔들린다.

총평:
- 특히 비현대 배경 소설에 매우 강한 에이전트다.

### 10. `repetition-checker.md`

파일:
- [repetition-checker.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/repetition-checker.md#L1)

평가:
- **GO**

강점:
- 반복을 죄악시하지 않는 점이 좋다.
- `5축 테스트`와 `WATCH` 운영은 실용적이다.
- 모티프와 습관적 반복을 구분하려는 태도가 건강하다.

리스크:
- `style-lexicon`, `decision-log`, `episode-log` 태그가 비어 있거나 부실하면 성능이 급락한다.

총평:
- 보이스 보호 측면에서 좋은 설계다.

### 11. `narrative-reviewer.md`

파일:
- [narrative-reviewer.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/narrative-reviewer.md#L1)

평가:
- **GO**

강점:
- “이 소설이 아직 좋은가”만 본다는 정체성이 분명하다.
- `WTF moments`, `single biggest structural problem`, `agency`, `scale inflation`, `thematic drift`를 직접 본다.
- arc 단위 개발편집기로 매우 적합하다.

리스크:
- 결과물이 `narrative-fixer` 경로에 강하게 묶여 있다.
- hybrid에서 실제 수정 주체가 Codex라면 후속 실행 문서와의 연결을 다시 써야 한다.

총평:
- 진단기로는 강하다.
- 후속 적용 경로만 hybrid 기준으로 손보면 된다.

### 12. `narrative-fixer.md`

파일:
- [narrative-fixer.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/narrative-fixer.md#L1)

평가:
- **REVISE**

강점:
- “surgeon, not author” 원칙이 명확하다.
- WHY/OAG/repetition/POV-era/scene-logic 등 source별 세분화가 잘 되어 있다.
- HOLD 승격 규칙도 보수적이라 안전하다.

리스크:
- hybrid 현재상에는 실행 주체가 어긋난다.
- 사용자 승인 게이트와 직접 본문 수정 전제가 자동 파이프라인과 충돌할 수 있다.

총평:
- 사고 방식은 아주 좋다.
- 하지만 이 문서는 지금 상태로는 “Claude fixer”용이지 “현재 hybrid 실행 fixer”용은 아니다.

### 13. `plot-surgeon.md`

파일:
- [plot-surgeon.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/plot-surgeon.md#L1)

평가:
- **REVISE**

강점:
- OAG의 `plot-change-needed`를 별도 수선 계층으로 분리한 발상은 맞다.
- `Step 0 플롯 맥락`, `보존 불변식`, `영향 매트릭스`는 매우 좋다.

리스크:
- 승인 규칙이 내부적으로 충돌한다.
- 외부 AI와 lean형 writer handoff를 아직 전제로 둔다.
- 현재 hybrid에서 가장 stale한 축이다.

총평:
- 개념은 좋지만, 가장 먼저 정리해야 할 문서다.

### 14. `story-consultant.md`

파일:
- [story-consultant.md](/root/novel/claude-codex-novel-templates-hybrid/.claude/agents/story-consultant.md#L1)

평가:
- **GO**

강점:
- 컨셉 단계에서 AI 장편 집필 실패를 미리 예측하는 설계가 좋다.
- 7개 렌즈가 서로 겹치지 않고, 특히 `AI 실패 예측자`와 `주제/의미 편집자`가 유효하다.
- “안전한 평작보다 위험한 걸작 후보”를 선호하는 철학도 좋다.

리스크:
- 출력이 파일이 아니라 inline이라 프로젝트 기록성이 약하다.

총평:
- 초기 컨셉 설계용으로 매우 좋다.
- 실무상으로는 결과를 파일에도 남기면 더 강해진다.

---

## 전체 평점

| 구분 | 평가 |
|------|------|
| 진단 계열 | 강함 |
| 개발편집 계열 | 강함 |
| 수정 계열 | 부분 stale |
| hybrid 정합성 | 대체로 양호, fix/plot 축 재정렬 필요 |
| 소설 품질 기여도 | 높음 |

---

## 우선 수정 추천

1. `plot-surgeon`에서 `사용자 승인 필수`와 `AUTO-APPROVED` 중 하나만 남겨 기준을 통일.
2. `plot-surgeon`의 `writer`/`narrative-fixer` handoff를 현재 hybrid의 `Codex writer/fixer` 기준으로 다시 작성.
3. `narrative-fixer`를 “Claude diagnosis + Codex execution” 구조에 맞게 분해하거나, 문서 상단에 `legacy fixer logic / execution via Codex`를 명시.
4. `why-checker`에서 OAG와 겹치는 질문 카테고리를 정리.
5. `story-consultant` 결과를 inline만이 아니라 파일로도 남기도록 확장 검토.

---

## 결론

이 저장소의 에이전트 세트는 전반적으로 수준이 높다. 특히 “AI가 쓰면 어디서 망가지는가”를 잘 알고 만든 흔적이 있다.

지금 문제가 되는 건 대부분 **검사 에이전트의 품질**이 아니라 **수정 에이전트와 hybrid 실행 주체 사이의 정합성**이다. 진단 계열은 이미 충분히 쓸 만하고, fix/plot 계열 두세 개만 현재 운영 구조에 맞게 다시 묶으면 전체 체계 완성도가 많이 올라간다.
