캐릭터가 정보를 알면서도 당연한 행동을 하지 않는 의무 행동 갭(OAG)을 탐지한다.

## 사용법

```
/oag-check                  # 전체 소설 (Text Mode)
/oag-check arc-01           # 특정 아크만
/oag-check 1-5              # 범위 지정
/oag-check plan arc-01      # 플롯 사전 검증 (Planning Mode)
/oag-check plan             # 전체 플롯 사전 검증
```

## Text Mode (기본)

1. `.claude/agents/oag-checker.md`를 읽고 지시에 따른다.
2. `settings/03-characters.md`에서 캐릭터 성격을 읽는다.
3. 에피소드 본문을 순서대로 읽으며 결정 노드를 추출한다.
4. **Generate-Then-Check**: 기대 행동을 먼저 생성하고, 그 다음 텍스트에서 확인한다.
5. **Phase 5.5 Fixability**: plot 파일을 참조하여 patch-feasible / plot-change-needed 판정.
6. 산출물: `summaries/oag-report.md`

## Planning Mode (`plan`)

집필 전 플롯 단계에서 동기 갭을 미리 탐지한다. 집필 후 잡으면 플롯 재설계가 필요하지만, 여기서 잡으면 플롯 문장 1줄로 해결된다.

1. `.claude/agents/oag-checker.md`의 Planning Mode 절차를 따른다.
2. `plot/arc-{NN}.md` + `plot/master-outline.md` + `settings/03-characters.md`를 읽는다.
3. 플롯 요약에서 결정 노드를 추출하고, 동기 경로를 검증한다.
4. 산출물: `summaries/oag-check-plan-{arc}.md`
