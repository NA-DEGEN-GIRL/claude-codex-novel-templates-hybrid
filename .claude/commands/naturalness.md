한국어 자연스러움을 전수 검사한다. Claude(korean-naturalness) + GPT(결합 자연성) 이중 검사.

## 사용법

`/naturalness` 또는 `/naturalness N-M`

- 인자 없음: 전체 에피소드 검사
- 범위: 해당 화수만 검사

## 1단계: Claude korean-naturalness

> **각 에피소드마다 별도의 Agent를 호출한다.**
> 하나의 Agent가 여러 화를 연속 처리하면 주의력이 떨어져서 어색한 표현을 놓친다.

절차:

1. 에피소드 파일 목록을 수집한다 (chapters/**/*.md, 번호순 정렬)
2. **각 에피소드마다** 아래를 반복:
   ```
   Agent(korean-naturalness: {N}화 검사)
   → .claude/agents/korean-naturalness.md를 읽고
   → chapters/{arc}/chapter-{N}.md 1개만 읽고
   → 어색한 표현을 찾아 보고
   ```
3. 각 Agent의 결과를 수집하여 `summaries/naturalness-report.md`에 통합 저장. **모든 에피소드의 상세 테이블을 빠짐없이 포함한다.** `/naturalness-fix`가 이 보고서만 보고 수정하므로, 상세가 없으면 수정 불가.

주의:
- **절대로 한 Agent가 여러 화를 처리하지 않는다.**
- 동시에 여러 Agent를 병렬 실행해도 된다 (각각 1화만 담당하므로).

## 2단계: (hybrid에서는 생략)

> **hybrid 파이프라인**: GPT가 집필하므로 GPT naturalness 검사는 제거.
> Claude korean-naturalness 단독 검사로 충분. GPT 글을 Claude가 읽으므로 교차 검증 효과.

## 출력

`summaries/naturalness-report.md`에 통합:

```markdown
### {N}화 — 자연스러움

| # | 위치 | 원문 | 왜 어색한가 | 수정 방향 | 예시 |
|---|------|------|-----------|-----------|------|
```
