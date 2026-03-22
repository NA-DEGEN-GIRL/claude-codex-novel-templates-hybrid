# Claude × GPT Hybrid Pipeline Design

## Architecture

```
Claude Code (Orchestrator)          GPT 5.4 (Prose Engine)
─────────────────────────          ─────────────────────────
Step 1: compile_brief
Step 2: Read previous ep
Step 3: Check feedback
Step 4: Planning gate
Step 5: Reader objection

       ─── writer_packet.md ──→
                                   Step 6: Write prose draft
       ←── chapter-{NN}.md ───

Step 7: Self-review (Claude)
Step 8-9: Summary update
Step 10: Unified review + external
Step 11: EPISODE_META
Step 12: Git commit

  ─── rewrite request (optional) ──→
                                   Step 6b: Partial rewrite
  ←── revised segment ────────
```

## Key Principles

1. **Claude = stateful orchestrator** — 파이프라인 제어, 연속성 관리, 검증
2. **GPT = prose engine** — 본문 생성만. 프로젝트 상태를 직접 읽지 않음
3. **writer_packet이 유일한 인터페이스** — Claude가 압축한 패킷만 GPT에 전달

## writer_packet.md 구조

```markdown
# Writer Packet — {N}화

## 소설 정보
- 제목: {title}
- 장르: {genre}
- Voice Profile: {§0 전문}
- 대표 문단: {§0.3 전문}

## 이번 화 목표
- 서사 목표: {1-2문장}
- 엔딩 훅 타입: {cliffhanger/reveal/decision/emotion/calm/question}
- 주제 연결: {thematic function}

## 장면 비트 (5-8개)
1. {장면 1 설명}
2. {장면 2 설명}
...

## 등장인물 (이번 화)
{character 슬라이스 — 이름, 성격/말투, 대표 대사}

## 직전 화 끝 (2-3문단)
{previous episode last paragraphs}

## 불변 조건 (반드시 준수)
{Continuity Invariants table}

## 금지 패턴
- 외래어 금지 (비현대): 에너지→기운, 시스템→체계, ...
- 아라비아 숫자 금지 (비현대)
- 메타 표현 금지: "N화에서", "독자 여러분"
- 전생 비교문 2회 이하
- {소설별 추가 금지}

## 출력 규격
- 한국어만 출력
- 본문만 출력 (EPISODE_META, 요약 등 불필요)
- 분량: {min}~{max}자
- 장면 구분: ***
- 파일 저장: {output_path}
```

## write_episode MCP 도구

```python
write_episode(
    novel_dir: str,          # 소설 폴더 경로
    episode_number: int,     # 화 번호
    writer_packet_path: str, # writer_packet.md 경로
    output_path: str,        # 출력 파일 경로
    mode: str = "draft",     # "draft" | "rewrite_segment"
    target_range: str = None, # rewrite 시 수정 범위 (줄 번호)
    model: str = "gpt-5.4",
) -> {
    status: str,
    output_path: str,
    char_count: int,
    token_usage: dict,
    latency_ms: int,
}
```

내부 구현: codex CLI 호출
```bash
codex exec - --full-auto -m gpt-5.4 \
  -c model_reasoning_effort="high" \
  -C {novel_dir} \
  < writer_packet.md
```

## 검증/수정 루프

1. GPT 초안 → Claude unified-review
2. 발견된 이슈 분류:
   - **연속성/설정 위반**: Claude narrative-fixer가 직접 수정
   - **prose 품질 (전투, 대사, 감정)**: GPT에 부분 재작성 요청 (1회 한정)
3. GPT 재시도 1회 + Claude 최종 patch → 완료
4. 무한 루프 금지: 최대 GPT 2회 호출 (draft + rewrite_segment 1회)

## 비용 추정 (화당)

| 항목 | 토큰 | 비용 (gpt-5.4 기준) |
|------|------|---------------------|
| writer_packet 입력 | ~10K | ~$0.025 |
| 본문 출력 | ~12K | ~$0.18 |
| rewrite (50% 확률) | ~8K | ~$0.12 |
| **화당 평균** | | **~$0.25** |

## TODO

- [ ] mcp-novel-editor에 write_episode 도구 구현
- [ ] writer.md step 6을 GPT 위임으로 수정
- [ ] writer_packet 생성 함수 구현 (compile_brief.py 확장 또는 별도)
- [ ] GPT_WRITER.md — GPT 전용 집필 지침 (writer_packet에 내장)
- [ ] batch-supervisor.md 프롬프트 템플릿 수정
- [ ] 001-hybrid 소설로 테스트
