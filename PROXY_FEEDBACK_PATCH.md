# Proxy Feedback Patch

Date: 2026-04-07

## Goal

`proxy_feedback`를 단순 표면 교정기에서 **한국어 line-level 감수기**로 확장했다.

핵심 방향:
- continuity / plot / worldbuilding 리뷰는 여전히 하지 않는다.
- 대신 한국어 원어민 기준의 **읽힘, 결합 자연성, 과압축, 문단 마감 문장 품질**까지 본다.

## What Changed

### 1. Runtime prompt expanded

Patched file:
- `/root/novel/mcp-novel-editor/editor_server.py`

`build_proxy_prompt()`를 아래 범위를 보도록 확장했다.
- 번역투
- 어색한 결합/호응/격틀
- 과압축/멋부린 문장
- 비의도 반복
- 서술 register 흔들림
- 대사의 표면 자연스러움(명백한 경우만)
- 확실한 맞춤법/띄어쓰기/문장부호

### 2. Output structure upgraded

기존:
- 단일 표, 최대 10건

변경 후:
- `MUST-FIX` 최대 12건
- `WATCHLIST` 최대 5건
- `GLOBAL PATTERNS` 최대 3건

의도:
- 지금 고쳐야 하는 것과, 반복되면 위험한 패턴을 분리
- 한 화 전체에서 드러나는 line-level 경향도 남기기

### 3. System prompt tightened

`call_proxy()`의 system prompt를 아래 방향으로 강화했다.
- line editor 역할 명시
- 서사 평론 금지
- 최소 수정안 우선
- 애매하면 지적 금지

### 4. Hybrid docs updated

Patched files:
- `/root/novel/claude-codex-novel-templates-hybrid/CLAUDE.md`
- `/root/novel/claude-codex-novel-templates-hybrid/HYBRID-DESIGN.md`

문서상 `Proxy` 역할을 다음처럼 재정의했다.
- 한국어 자연스러움
- 결합/호응
- 반복
- 과압축
- 첫 문장/장면 전환/문단 마지막 문장의 읽힘

## What Did Not Change

아래 항목은 여전히 `proxy_feedback` 범위 밖이다.
- continuity 검증
- 설정/세계관/플롯 판단
- 감정선/캐릭터 아크 비평
- 전체 문단/장면 리라이트
- 캐릭터 고유 말투의 표준화

이 영역은 계속 Claude unified-reviewer, Gemini, why-check, OAG-check, scene-logic-check 쪽이 맡는다.

## Operational Intent

권장 역할 분담:
- NIM/Ollama: 철자/문법/문장부호
- Proxy: 한국어 line-level 읽힘, 번역투, 결합 자연성, 과압축, 반복
- Claude unified-reviewer: continuity + narrative decision
- Gemini/GPT: 교차 모델 시각

즉 Proxy는 "작은 NIM"이 아니라, **한국어 line editor**로 운용하는 것이 목적이다.
