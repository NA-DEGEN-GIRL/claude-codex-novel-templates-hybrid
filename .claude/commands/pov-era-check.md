시점 지식 위반 + 시대 부적합 표현을 전수 검사한다.

## 사용법

`/pov-era-check` 또는 `/pov-era-check N-M`

- 인자 없음: 전체 에피소드 검사
- 범위: 해당 화수만 검사

## 절차

> **각 에피소드마다 별도의 Agent를 호출한다.**
> 하나의 Agent가 여러 화를 연속 처리하면 주의력이 떨어진다.

1. 에피소드 파일 목록을 수집한다 (chapters/**/*.md, 번호순 정렬)
2. compile_brief를 호출하여 knowledge-map + worldbuilding 규칙을 확보한다
3. **각 에피소드마다** 아래를 반복:
   ```
   Agent(pov-era-checker: {N}화 검사)
   → .claude/agents/pov-era-checker.md를 읽고
   → knowledge-map 슬라이스 + worldbuilding 규칙 + chapters/{arc}/chapter-{N}.md를 읽고
   → 시점 지식 위반 + 시대 부적합 표현을 찾아 보고
   ```
4. 각 Agent의 결과를 수집하여 `summaries/pov-era-report.md`에 통합 저장

주의:
- **절대로 한 Agent가 여러 화를 처리하지 않는다.**
- 동시에 여러 Agent를 병렬 실행해도 된다 (각각 1화만 담당하므로).
- knowledge-map 슬라이스는 해당 화의 POV 인물 + 등장 인물 기준으로 추출한다.

## 출력

`summaries/pov-era-report.md`에 통합:

```markdown
## 시점·시대 감사 보고서

### {N}화
#### A. POV 지식 감사 ({POV 인물명})
| # | 유형 | 위치 | 원문 | 왜 부적합한가 | 수정 방향 |
|---|------|------|------|-------------|-----------|

#### B. 시대 적합성 감사
| # | 유형 | 위치 | 원문 | 왜 부적합한가 | 수정 방향 |
|---|------|------|------|-------------|-----------|
```

## 후속 처리

❌ 항목이 있으면 `/narrative-fix --source pov-era`로 수정한다.
