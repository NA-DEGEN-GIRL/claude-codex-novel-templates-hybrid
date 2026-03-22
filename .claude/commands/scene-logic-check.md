장면 내부의 동작/시선/방향/자세 논리를 전수 검사한다.

## 사용법

`/scene-logic-check` 또는 `/scene-logic-check N-M`

- 인자 없음: 전체 에피소드 검사
- 범위: 해당 화수만 검사

## 절차

> **각 에피소드마다 별도의 Agent를 호출한다.**
> 장면 논리는 에피소드 내부에서만 작동하므로 brief가 불필요하다.

1. 에피소드 파일 목록을 수집한다 (chapters/**/*.md, 번호순 정렬)
2. **각 에피소드마다** 아래를 반복:
   ```
   Agent(scene-logic-checker: {N}화 검사)
   → .claude/agents/scene-logic-checker.md를 읽고
   → chapters/{arc}/chapter-{N}.md 1개만 읽고
   → 장면별 물리 논리 모순을 찾아 보고
   ```
3. 각 Agent의 결과를 수집하여 `summaries/scene-logic-report.md`에 통합 저장

주의:
- **절대로 한 Agent가 여러 화를 처리하지 않는다.**
- 동시에 여러 Agent를 병렬 실행해도 된다 (각각 1화만 담당하므로).
- brief, settings 파일 읽기 불필요 — 본문만으로 검사.

## 출력

`summaries/scene-logic-report.md`에 통합:

```markdown
## 장면 논리 감사 보고서

### {N}화

#### 장면 1 ({위치/상황})
| # | 유형 | 위치 | 서술 내용 | 왜 모순인가 | 수정 방향 |
|---|------|------|----------|-----------|-----------|

#### 장면 2 (...)
...
```

## 후속 처리

❌ 항목이 있으면 `/narrative-fix --source scene-logic`로 수정한다.
