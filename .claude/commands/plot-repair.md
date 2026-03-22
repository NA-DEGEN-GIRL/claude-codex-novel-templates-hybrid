OAG 보고서의 plot-change-needed 항목에 대해 플롯을 수선한다.

## 사용법

```
/plot-repair                    # oag-report 기반 (기본)
/plot-repair OAG-01,OAG-04     # 특정 항목만
```

## 실행

1. `summaries/oag-report.md`가 없으면 `/oag-check`를 먼저 실행하라고 안내.
2. `plot-change-needed` 항목이 없으면 "수선 대상 없음"으로 종료.
3. `.claude/agents/plot-surgeon.md`를 읽고 지시에 따른다.
4. 수정안을 사용자에게 보여주고 승인을 받는다.
5. 승인 후 plot 파일 수정.
6. 재검증: `/oag-check plan` + `/why-check plan` 실행을 안내.
