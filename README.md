# 천외귀환 집필 세팅 (Claude × Codex Hybrid)

**이 저장소는 "완성된 범용 템플릿"보다, `천외귀환` 같은 한국어 웹소설을 실제로 집필하면서 계속 손보고 실험하는 작업 세팅에 가깝다.**

즉 이 README의 목적은 "이 구조가 정답이다"를 선언하는 데 있지 않다.  
오히려 다음을 전제로 한다.

- 먼저 한 작품을 실제로 써 본다
- 문체, 설정, 검토 흐름, tmux 감독 방식이 어디서 잘 되고 어디서 망가지는지 본다
- 그 결과를 프롬프트와 설정에 다시 반영한다
- 사용자가 자기 작품에 맞게 계속 수정한다

이 저장소는 그런 반복 실험을 버티도록 만든 **하이브리드 집필 베이스라인**이다.

---

## 이 저장소가 지향하는 것

`천외귀환`을 집필하며 확인한 전제는 단순하다.

- GPT 5.4/Codex는 한국어 본문 초안을 빠르게 잘 뽑을 수 있다
- 하지만 그대로 두면 설정 누수, 메타 표현, 장면 논리 누락이 생기기 쉽다
- Claude Code는 집필 자체보다 **감독, 리뷰, summary 정리, 후처리**에 더 강하다
- 좋은 결과는 "한 모델에게 다 시키기"보다 **역할을 나누고 계속 조정할 때** 나온다

그래서 이 저장소는 아래처럼 쓴다.

- **Codex / GPT 5.4**: 본문 집필, 부분 수정
- **Claude Code**: supervisor, 리뷰, summary, commit, 아크 경계 패키지
- **MCP 도구**: `compile_brief`, `novel-calc`, `novel-hanja`, `novel-editor` 등 검증/보조

핵심은 "모든 걸 자동화"가 아니라,  
**실제로 괜찮은 한국어 웹소설이 나오도록 집필 루프를 계속 조율하는 것**이다.

---

## 이 저장소는 템플릿이면서도 작업 로그다

이 저장소는 일반적인 의미의 "깨끗한 스타터 템플릿"과는 조금 다르다.

- `천외귀환` 집필 과정에서 발견된 문제들이 반영되어 있다
- writer 프롬프트, reviewer 규칙, tmux supervisor, MCP 사용 방식이 여러 번 수정되어 있다
- 어떤 규칙은 강화되었고, 어떤 규칙은 오히려 줄어들었다
- 즉 "처음부터 완벽한 설계"가 아니라 **실전에서 부딪히며 다듬은 결과**다

사용자는 이 저장소를 그대로 믿고 쓰기보다,  
**자기 작품을 실제로 한두 화 써 보면서 다시 바꾸는 것**을 전제로 삼는 편이 맞다.

예를 들어:

- 문장이 너무 과의식되면 writer를 더 lean하게 줄이고
- 설정 누수가 심하면 금지어/시점 체크를 짧게 더 붙이고
- review가 과하면 줄이고, 약하면 다시 올리고
- 분량이 늘어지면 목표 분량을 낮추고
- 너무 딱딱하면 Voice Profile이나 opening 규칙을 조정한다

이 README는 그 반복의 출발점이다.

---

## 권장 사용 방식

가장 추천하는 방식은 아래다.

1. 이 저장소를 새 소설 폴더로 복사한다
2. 작품 제목과 설정에 맞게 `CLAUDE.md`, `settings/`, `plot/`을 채운다
3. MCP를 등록한다
4. 몇 화를 실제로 써 본다
5. 결과를 보고 writer / review / supervisor를 다시 조정한다

즉 이 저장소는 "복사 후 그대로 고정 사용"보다,  
**복사 후 집필 → 관찰 → 수정 → 재집필** 루프에 더 잘 맞는다.

---

## 먼저 볼 파일

- [CLAUDE.md](./CLAUDE.md)
  이 작품/프로젝트의 최상위 규약
- [batch-supervisor.md](./batch-supervisor.md)
  Claude supervisor가 Codex writer를 감시하는 방식
- [INIT-PROMPT.md](./INIT-PROMPT.md)
  새 프로젝트 초기 세팅용
- [HYBRID-DESIGN.md](./HYBRID-DESIGN.md)
  왜 Claude와 Codex를 나눠 쓰는지
- [.claude/prompts/codex-writer-role.md](./.claude/prompts/codex-writer-role.md)
  writer의 기본 역할
- [.claude/prompts/codex-writer.md](./.claude/prompts/codex-writer.md)
  실제 집필 프롬프트 정본
- [.claude/prompts/codex-fixer.md](./.claude/prompts/codex-fixer.md)
  부분 수정 프롬프트
- [scripts/README.md](./scripts/README.md)
  tmux 보조 스크립트와 수동 테스트

처음 쓰는 사람에게는 이 순서를 권장한다.

1. 이 README
2. [CLAUDE.md](./CLAUDE.md)
3. [batch-supervisor.md](./batch-supervisor.md)
4. [.claude/prompts/codex-writer.md](./.claude/prompts/codex-writer.md)

---

## MCP 저장소 링크

이 세팅은 로컬 MCP 서버들과 함께 쓰는 전제를 깔고 있습니다.  
관련 저장소를 바로 열 수 있게 링크를 남겨 둡니다.

- [`mcp-novel-calc`](https://github.com/NA-DEGEN-GIRL/mcp-novel-calc)
- [`mcp-novel-editor`](https://github.com/NA-DEGEN-GIRL/mcp-novel-editor)
- [`mcp-novel-hanja`](https://github.com/NA-DEGEN-GIRL/mcp-novel-hanja)
- [`mcp-novel-naming`](https://github.com/NA-DEGEN-GIRL/mcp-novel-naming)
- [`mcp-novelai-image`](https://github.com/NA-DEGEN-GIRL/mcp-novelai-image)

---

## 구조 요약

```text
Claude Code (Supervisor / Review)
  ├─ tmux writer 세션 관리
  ├─ review floor 결정
  ├─ post-write 검증
  ├─ summary / EPISODE_META / commit
  └─ 아크 경계 패키지

Codex / GPT 5.4 (Writer / Fixer)
  ├─ compile_brief 호출
  ├─ plot / settings / 이전 화 읽기
  ├─ 본문 집필
  ├─ 부분 수정
  └─ WRITER_DONE / FIX_DONE sentinel 출력

MCP
  ├─ novel-editor
  ├─ novel-calc
  ├─ novel-hanja
  └─ novel-naming
```

이 구조의 장점은 역할이 분명하다는 점이다.

- writer는 본문에 집중
- reviewer/supervisor는 품질과 정합성에 집중
- 도구는 계산/검증 보조에 집중

---

## 왜 이렇게 나누는가

`천외귀환` 집필에서 가장 자주 보인 실패는 대체로 아래였다.

- writer가 설정까지 과하게 의식해서 문장이 과압축됨
- prose는 괜찮은데 금지어/메타 표현이 새어 나옴
- summary가 본문보다 앞서거나 뒤처져서 정합성이 깨짐
- tmux 감독이 애매한 timeout에 너무 의존함

그래서 한 세션에서 다 해결하려 하기보다,  
다음을 분리하는 편이 더 낫다는 결론에 도달했다.

- 생성
- 검증
- 요약 정리
- 배치 감독

이 저장소의 하이브리드 구조는 그 결론을 반영한 것이다.

---

## 중요한 태도

이 저장소를 쓸 때 제일 중요한 건, 규칙을 많이 넣는 것이 아니다.

오히려 다음이 더 중요하다.

- 실제로 한 화를 써 본다
- 이상한 문장이 어디서 생겼는지 본다
- 설정 누수가 왜 생겼는지 본다
- review가 너무 약한지, 너무 과한지 본다
- 그 결과에 맞춰 writer와 settings를 다시 조정한다

즉 좋은 소설은 README를 예쁘게 써서 나오는 게 아니라,  
**실제 집필 결과를 보고 프롬프트와 설정을 계속 바꾸면서** 나온다.

이 저장소는 그 반복을 위한 출발점이다.

---

## 빠른 시작

### 1. 새 프로젝트 생성

```bash
cp -r claude-codex-novel-templates-hybrid/ /root/novel/no-title-XXX/
cd /root/novel/no-title-XXX/
```

### 2. 작품 설정 채우기

- `CLAUDE.md`
- `settings/01~08`
- `plot/master-outline.md`
- 각 아크 플롯

### 3. MCP 등록

```bash
codex mcp add novel-calc -- python3 /root/novel/mcp-novel-calc/calc_server.py
codex mcp add novel-hanja -- python3 /root/novel/mcp-novel-hanja/hanja_server.py
codex mcp add novel-naming -- python3 /root/novel/mcp-novel-naming/naming_server.py
codex mcp add novel-editor -- python3 /root/novel/mcp-novel-editor/editor_server.py

codex mcp list
```

### 4. Supervisor 실행

```bash
cd /root/novel
claude
```

그 뒤 supervisor에게 소설 폴더와 세션 이름을 주고 `batch-supervisor.md` 규칙대로 집필을 돌리면 된다.

---

## 권장 운영 방식

이 저장소는 처음부터 완성된 상태로 굴리기보다, 아래처럼 쓰는 편이 좋다.

1. 프롤로그나 1~3화를 먼저 써 본다
2. prose가 과한지, 평평한지 본다
3. 설정/시점/메타 누수가 생기는지 본다
4. writer를 줄일지, review를 늘릴지 결정한다
5. 다시 써 본다

특히 `천외귀환`처럼:

- 무협 + SF 혼합
- 회귀
- 사파 악인 시점
- 건조하지만 읽혀야 하는 문체

같이 균형이 어려운 작품일수록,  
한 번에 맞추기보다 여러 번 시도하면서 조율하는 편이 낫다.

---

## 마지막으로

이 저장소는 "하이브리드 소설 집필의 최종 답안"이 아니다.

지금은 `천외귀환`을 집필할 수 있을 정도로 정리된 상태고,  
앞으로도 사용자들이:

- writer를 더 줄이거나
- review를 더 강화하거나
- Voice Profile을 조정하거나
- tmux 감독 방식을 손보거나
- MCP 사용 규칙을 바꾸면서

계속 업데이트해 나가야 한다.

좋은 결과가 나오면 그 변화는 다시 문서와 프롬프트로 환원하면 된다.  
이 README는 그 반복을 권장하는 문서다.
