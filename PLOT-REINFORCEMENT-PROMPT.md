# 전체 플롯 강화 프롬프트

> `/root/novel/`에서 Claude Code 또는 Codex를 열고, `INIT-PROMPT.md`로 초기 세팅을 마친 hybrid 소설 프로젝트 안에서 아래 프롬프트를 붙여넣는다.
> 목표는 초기 `plot/`을 집필 직전 수준의 상세도로 강화해, writer와 `compile_brief`가 바로 활용할 수 있게 만드는 것이다.
> 이 작업은 구조 설계 단계이므로 `high` 이상, 가능하면 `xhigh` effort를 권장한다.

## 사용법

```bash
cd /root/novel/no-title-XXX
```

- Claude를 쓸 때: `claude`
- Codex를 쓸 때: `codex`

아래 프롬프트를 그대로 붙여넣고 `[대괄호]` 값만 바꿔 쓴다.

## 프롬프트

```text
현재 `/root/novel/no-title-XXX` hybrid 소설 프로젝트의 `plot/`과 `settings/`를 읽고, 집필용으로 충분히 상세한 plot 문서 세트를 만들어줘.

## 대상

- 프로젝트: [no-title-XXX]

## 범위

- 이번 작업은 `plot/` 강화가 핵심이다.
- 에피소드 본문은 쓰지 마라.
- `settings/`는 읽기만 하고, 모순이 너무 커서 plot만으로 해결할 수 없을 때만 마지막에 리스크로 보고하라.
- `summaries/`는 수정하지 마라.
- `full_story.md`는 읽을 수는 있지만, 이번 작업에서 수정하지 마라.

## 우선 기준

- `CLAUDE.md`가 있으면 최우선 기준으로 삼아라.
- `CODEX.md`가 함께 있으면 보조 기준으로 읽되, 충돌 시 `CLAUDE.md` 우선으로 정리하라.
- 이미 적혀 있는 핵심 컨셉, 장르 약속, 주인공 축, 결말 방향은 존중하라.
- 다만 현재 plot이 너무 느슨하면, 집필 가능한 수준까지 구체화하고 인과를 보강하라.

## 반드시 읽을 파일

- `CLAUDE.md`
- `CODEX.md` (if present)
- `full_story.md` (if present)
- `plot/master-outline.md`
- `plot/prologue.md` (if present)
- `plot/arc-*.md`
- `plot/interlude*.md` (if present)
- `plot/epilogue.md` (if present)
- `plot/foreshadowing.md` (if present)
- `plot/timeline.md` (if present)
- `settings/01-style-guide.md`
- `settings/02-episode-structure.md`
- `settings/03-characters.md`
- `settings/04-worldbuilding.md`
- `settings/05-continuity.md`
- `settings/07-periodic.md`

## 진행 순서

1. 먼저 현재 plot의 약한 지점을 진단한다.
   - arc 경계가 흐린가
   - 주인공 목표와 전개가 느슨하게 연결되는가
   - escalation 이유가 약한가
   - 관계 변화가 사건에 묶이지 않았는가
   - 복선과 회수 계획이 비어 있는가
   - 초반 10화 내 훅과 런웨이가 약한가
2. 그 진단을 바탕으로 `plot/master-outline.md`를 강화한다.
3. master outline에 적힌 각 아크/프롤로그/에필로그를 실제 집필 가능한 상세 plot 파일로 풀어쓴다.
4. `plot/foreshadowing.md`를 설치/회수 기준으로 정리한다.
5. 시간축이 중요한 작품이면 `plot/timeline.md`도 만든다.
6. 마지막으로 `compile_brief.py` 기준으로 실제로 읽히는 형식인지 확인한다.

## 강한 제약

- 핵심 컨셉을 다른 작품처럼 바꾸지 마라.
- 장르 쾌감을 흐리는 generic filler arc를 넣지 마라.
- "그리고 다음엔 또 다른 사건이 생긴다" 식의 나열형 전개로 두지 마라. 원인, 대가, 후속 압박이 보여야 한다.
- 주요 아크마다 반드시 다음이 보여야 한다:
  - 주인공의 목표
  - 목표를 가로막는 압박
  - 중간 전환점 또는 폭로
  - 감정/관계 변화
  - 아크 종료 시 달라진 판
- 복선은 심기만 하지 말고, 어디서 어떻게 회수될지 기본 배선을 잡아라.
- 관계 변화는 "친해짐/멀어짐" 같은 라벨만 두지 말고, 어떤 사건 때문에 그렇게 바뀌는지 써라.
- 회상, 수련, 잠입, 조사, 여행 같은 전개는 왜 필요한지 기능이 분명해야 한다.
- plot에 없는 사실을 멋대로 세계관 정설로 확정하지 마라. 필요한 구체화는 기존 설정 안에서 하라.
- 코어 premise, 주인공 교체, 장르 축 변경, 최종 결말 축 변경이 필요하다고 판단되면 거기서 멈추고 사용자 승인 포인트로 보고하라.

## 필수 산출물

### 1. `plot/master-outline.md`

- 전체 아크 구성을 더 선명하게 만든다.
- 각 아크마다 최소한 아래가 보이게 한다:
  - 아크 제목
  - 화수 범위
  - 핵심 갈등
  - 시작 상태
  - 핵심 전환점
  - 클라이맥스/결정적 선택
  - 종료 후 남는 상태 변화
- 가능하면 `성공-대가 연쇄`도 실제 작품 내용으로 채운다.

### 2. `plot/{arc}.md`

- `master-outline`에 적힌 각 아크마다 실제 상세 plot 파일을 만든다.
- 필요 시 `prologue.md`, `arc-01.md`, `arc-02.md`, `interlude-01.md`, `epilogue.md` 같은 형식으로 만든다.
- 각 파일은 최소한 아래 구조를 포함하라:
  - 아크 목적/장르 약속
  - 시작 상태
  - 종료 상태
  - 중간 전환점
  - 에피소드별 계획 표

### 3. 에피소드별 계획 표 형식

- `compile_brief.py`가 읽을 수 있게, 각 row의 앞 4개 의미를 반드시 아래 순서로 유지하라:
  - `화`
  - `목표`
  - `훅 타입`
  - `핵심 장면`
- 그 뒤에 필요한 열을 추가하는 것은 가능하다. 예:
  - `감정 변화`
  - `관계 변화`
  - `risk`
  - `비고`

### 4. `plot/foreshadowing.md`

- 복선을 단순 메모가 아니라 운용 가능한 계획표로 정리하라.
- 최소 항목:
  - ID
  - 복선 내용
  - 설치 시점
  - 회수 예정 시점
  - 중간 진전
  - 현재 상태
  - 비고

### 5. `plot/timeline.md` (조건부)

- 날짜, 이동 시간, 수련 기간, deadline, 회상 연표가 중요하면 생성/보강하라.
- 시간축이 plot 기능에 영향을 주는 작품이면 이 파일을 비워두지 마라.

## 품질 기준

- 첫 5화는 독자가 왜 다음 화를 눌러야 하는지 명확해야 한다.
- 첫 아크는 "세계/관계/갈등/장르 쾌감"이 동시에 굴러가야 한다.
- 중반 아크는 단순 반복이 아니라 판의 크기나 의미가 달라져야 한다.
- 마지막 아크는 초반 약속, 중반 확대, 후반 폭로가 한 줄기로 수렴해야 한다.
- writer가 `plot/{arc}.md`만 읽어도 각 화의 기능과 방향을 바로 이해할 수 있어야 한다.

## 검증

- 작업 후 `compile_brief.py`를 최소 2개 화수에 대해 점검하라.
- 첫 집필 화수와, 그 다음 중요한 시작 화수 하나를 골라 `이번 화 목표`가 비어 있지 않은지 확인하라.
- `compile_brief`가 plot을 제대로 못 읽는 형식이면 표/헤더를 수정해서 맞춰라.

## 최종 보고

- 수정/생성한 `plot` 파일 목록
- 강화된 핵심 포인트
- 남아 있는 구조 리스크
- 바로 집필에 들어가도 되는지 여부
- 다음 권장 순서
  - `FULL-STORY-PROMPT.md` 실행 여부
  - `batch-supervisor.md` 진입 여부
```
