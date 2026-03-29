# 전체 줄거리 생성 프롬프트

> `/root/novel/`에서 Claude Code 또는 Codex를 열고, 이미 셋업된 hybrid 소설 프로젝트 안에서 아래 프롬프트를 붙여넣는다.
> 목표는 `plot/`과 `settings/`를 읽고 프로젝트 루트의 `full_story.md`를 생성하거나 강화하는 것이다.

## 사용법

```bash
cd /root/novel/[소설 폴더]
```

- Claude를 쓸 때: `claude`
- Codex를 쓸 때: `codex`

아래 프롬프트를 그대로 붙여넣고 `[대괄호]` 값만 바꿔 쓴다.

## 프롬프트

```text
현재 hybrid 소설 프로젝트의 `plot/`과 `settings/`를 전부 읽고, 작품 전체 줄거리를 충분히 상세하게 정리한 `full_story.md`를 만들어줘.

## 대상

- 프로젝트: [no-title-XXX]

## 우선 기준

- 상위 운영 문서가 `CLAUDE.md`면 그것을 최우선으로 반영한다.
- Codex로 작업하더라도 `CODEX.md`가 따로 없다면 `CLAUDE.md`와 `settings/` 기준으로 정리한다.
- 이 문서는 집필 전용 참고 문서이므로, plot과 settings의 공통 분모를 읽기 좋게 통합해야 한다.

## 반드시 읽을 파일

- `CLAUDE.md`
- `plot/prologue.md` (있으면)
- `plot/master-outline.md`
- `plot/arc-*.md`
- `plot/foreshadowing.md`
- `plot/timeline.md` (있으면)
- `settings/01-style-guide.md`
- `settings/02-episode-structure.md`
- `settings/03-characters.md`
- `settings/04-worldbuilding.md`
- `settings/05-continuity.md`
- `settings/06-humor-guide.md` (있으면)
- `settings/07-periodic.md`

## 작성 원칙

- 기존 `full_story.md`가 있으면 먼저 읽고, 정보 밀도와 가독성을 높이는 방향으로 전면 갱신하라.
- `plot`에 적힌 사건을 기계적으로 옮기지 말고, 주제와 감정선이 같이 읽히게 재구성하라.
- 세계관의 핵심 진실, 인물 관계 변화, 각 부의 에스컬레이션 이유가 드러나야 한다.
- 주요 반전과 복선 회수는 독자가 왜 강하게 느끼는지까지 설명하라.
- 결과물만 읽어도, 소설 본문을 직접 읽지 않은 사람이 전체 줄거리와 주요 반전, 관계 변화, 결말의 의미를 충분히 이해할 수 있어야 한다.
- 과도한 메모체, 표 중심 요약, 화수 나열만으로 끝내지 마라.
- 그렇다고 소설 본문처럼 미사여구를 늘어놓지 말고, 기획 문서로서 선명하게 써라.
- `plot/`에 없는 세부를 함부로 확정하지 말고, 불확실하면 범주형 표현으로 정리하라.
- 결과는 반드시 한국어로 쓴다.
- 아래 같은 설명용 문구나 인용 블록은 결과물에 넣지 마라:
  `plot/`, `settings/`, `CLAUDE.md`를 바탕으로 정리한 작품 전체 줄거리.
  단순 시놉시스가 아니라, 작품의 장르적 재미, 정체성 미스터리, 감정축, 우주적 스케일, 마지막 선택까지 모두 한 번에 읽히도록 상세하게 서술한다.
- 결과 문서는 곧바로 제목이나 첫 섹션부터 시작하라.

## 권장 구성

1. 작품 개요
2. 프롤로그 요약
3. 1부 전체 줄거리
4. 2부 전체 줄거리
5. 3부 전체 줄거리
6. 에필로그 요약 (있으면)
7. 이 이야기의 재미 포인트

## 최종 작업

- 프로젝트 루트에 `full_story.md`를 저장하라.
- 필요하면 기존 파일을 덮어써라.
- 이번 작업에서는 `plot/`, `settings/`, `summaries/`를 수정하지 마라.
- 다만 읽는 중 구조적 구멍이나 보강 필요 지점이 명확하게 보이면, 문서 작성 후 마지막에 짧게 메모하라.
```
