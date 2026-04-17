# Claude Handoff — Fresh-Session Continuity Patch

## 목적

Writer가 fresh session처럼 동작하거나 auto-compact로 오래된 세부 맥락이 압축돼도, 다음 화 오프닝 continuity가 무너지지 않도록 템플릿 레벨에서 carry-forward 앵커를 강화했다.

## 변경 파일

- `compile_brief.py`
- `.claude/prompts/claude-writer.md`
- `.claude/agents/unified-reviewer.md`
- `CLAUDE.md`
- `batch-supervisor.md`
- `summaries/running-context.md`
- `summaries/knowledge-map.md`

## 핵심 변경

1. `compile_brief.py`
   - `plot/prologue.md`, `plot/epilogue.md`, `plot/arc-*.md`, `plot/interlude*.md`를 읽는다.
   - `## N화` 형식과 `| 화 | 목표 | 훅 타입 | 핵심 장면 |` 표 형식을 둘 다 지원한다.
   - table-based `episode-log.md`를 읽는다.
   - 직전 화 `EPISODE_META.characters_appeared`를 fallback으로 쓴다.
   - 브리프에 `## 직전 화 직결 앵커`를 추가해, 직전 화 마지막 장면과 오프스크린 점프 금지 규칙을 같이 넣는다.
   - `running-context.md`의 `Immediate Carry-Forward` 섹션을 읽는다.

2. writer prompt
   - 직전 화는 "마지막 2~3문단"이 아니라 "마지막 장면 전체 또는 마지막 8~12문단" 기준으로 읽는다.
   - 집필 전 메모에 carry-forward 사실, 공개/비공개 정보, 완료/미완료 조치를 의무화했다.
   - 보고, 허락, 안심, 소문 확산, 관아 전달, 관계 변화를 본문 밖에서 이미 끝난 일처럼 쓰지 못하게 막았다.

3. reviewer
   - `Opening carry-forward gate`를 추가했다.
   - 현재 화 첫 장면이 직전 화 마지막 장면의 공개 정보, 미공개 정보, 미완료 조치를 건너뛰면 최소 `⚠️`, 명백 충돌이면 `❌`로 본다.

4. summary / supervisor rule
   - `running-context.md`에 `Immediate Carry-Forward` 또는 `직전 화 직결 상태`를 유지하도록 했다.
   - `knowledge-map.md`는 "누가 무엇을 배웠는가"뿐 아니라, 보고/경고/허락/소문/비밀 공유가 실제로 성립했거나 불발된 경우도 기록하도록 했다.
   - supervisor 문서의 `/clear 필수` 전제를 걷어내고, auto-compact 우선으로 바꿨다. `/clear`는 선택적 recovery 수단이다.

## Claude가 다음부터 지킬 점

- 현재 화 오프닝은 반드시 `compile_brief`의 `직전 화 직결 앵커`와 `running-context.md`의 `Immediate Carry-Forward`를 먼저 본다.
- 직전 화에 텍스트로 보이지 않은 보고/허락/안심/전달/소문 확산을 다음 화 기정사실로 쓰지 않는다.
- review 후 summary 갱신 시 아래 두 개를 특히 챙긴다.
  - `running-context.md`: 다음 화 오프닝에 필요한 직결 상태 3~7개
  - `knowledge-map.md`: 누가 알았는지/모르는지/전달이 됐는지 안 됐는지

## 검증 포인트

- `compile_brief`가 프롤로그/에필로그/아크 표 형식 플롯을 모두 읽는지
- `compile_brief`에 `직전 화 직결 앵커`가 붙는지
- table형 `episode-log.md`를 최근 화 요약으로 다시 압축하는지
- `python3 -m py_compile compile_brief.py`가 통과하는지

## 남은 리스크

- 실제 프로젝트에 `knowledge-map.md`, `dialogue-log.md`, `relationship-log.md`를 비워 둔 채 시작하면 carry-forward 검증력이 약해진다.
- 이 패치는 "다음 화 오프닝 jump 방지"가 핵심이다. 프로젝트 시작 후 summaries backfill discipline이 따라와야 효과가 유지된다.
