# 소설 재구축 프롬프트 (Rebuild)

> hybrid 마이그레이션 완료 후, 세계관/플롯을 재정립하고 기존 원고를 아카이브한 뒤 처음부터 다시 집필한다.
> MIGRATION-PROMPT.md 실행 후 사용하는 것이 전제.

---

## 언제 사용하는가

- 초기 세팅이 검증 없이 만들어져서 설정 구멍이 많은 경우
- 기존 집필 품질이 신인상/출판 목표에 미달하는 경우
- hybrid 시스템(why-check, story-consultant 등)으로 처음부터 탄탄하게 다시 짜고 싶은 경우
- 핵심 컨셉은 좋지만 실행이 아쉬운 경우

---

## 사용법

```bash
cd /root/novel && claude
```

아래 프롬프트를 붙여넣는다.

---

## 프롬프트

```
no-title-{XXX}/ 소설을 재구축(rebuild)한다. 핵심 컨셉은 살리되, 세계관/플롯/설정을 재정립하고 처음부터 다시 집필할 수 있도록 준비한다.

## 절대 보존
- 핵심 컨셉 (한줄 소개, 장르, 핵심 약속)
- 기존 원고 (아카이브로 보존)

## 절대 금지
- 기존 원고를 삭제하지 마라 (아카이브만)
- 핵심 컨셉 자체를 바꾸지 마라 (실행 방법만 개선)

## 진행 방식

### Phase 1: 기존 프로젝트 진단

#### 1-1. 핵심 컨셉 추출
기존 CLAUDE.md, settings/, plot/에서 다음을 추출하여 정리:
- 제목, 장르, 톤, 한줄 소개
- 핵심 약속 3가지
- 주인공 + 주요 캐릭터 (이름, 역할, 핵심 특징)
- 세계관 핵심 규칙
- 에피소드 엔진 (반복 루프)

#### 1-2. 기존 문제 진단
기존 원고를 실제로 읽는다. 설정 파일만으로는 진단이 불충분하다.
- **필독**: 1~3화 (독자 첫인상), 중반 대표 2화, 최근/완결부 2화
- **추가**: "가장 잘된 화 2개"와 "가장 문제인 화 2개"를 뽑아 원인 분석
- chapters-archive/가 아직 없으므로 현재 chapters/에서 읽는다

기존 원고와 설정을 읽고 다음을 진단:
- 설정 구멍 (why-check 관점)
- 플롯 구조 문제 (pacing, 스케일, 반전 설계)
- 캐릭터 문제 (능동성, 관계 엔진)
- 문체/톤 문제
- AI 집필 실패 패턴 (반복, 해설 과잉, 감정 직접 서술 등)

GPT 5.4에게도 진단을 맡긴다 (`mcp__external-ai__ask_gpt`):
"이 소설의 핵심 컨셉과 현재 문제점을 진단해주세요. 강점은 무엇이고 약점은 무엇인가? 재집필한다면 어떤 점을 개선해야 하는가?"

> ✅ 완료 기준: 강점 목록 + 약점 목록 + 보존 대상 + 개선 대상 명확

#### 1-3. 보존 명세서 작성
진단 결과를 기반으로 다음 표를 작성한다. **이 표가 이후 모든 단계의 기준이 된다.**

| 카테고리 | 유지 (절대 변경 금지) | 수정 (개선하되 핵심 보존) | 폐기 (새로 설계) |
|---------|---------------------|----------------------|----------------|
| 한줄 소개 | | | |
| 장르/톤 | | | |
| 핵심 약속 | | | |
| 주인공 | | | |
| 보조 캐릭터 | | | |
| 에피소드 엔진 | | | |
| 세계관 규칙 | | | |
| 문체 | | | |
| 아크 구조 | | | |

**사용자 승인 후 Phase 2로.**

> ✅ 완료 기준: 보존 명세서 사용자 승인

### Phase 2: story-consultant 재평가

#### 2-1. 7-Lens 평가
`.claude/agents/story-consultant.md`의 Step 2 (확장 컨셉 평가)를 실행한다.
- 기존 컨셉을 입력으로 7개 관점에서 재평가 (주제/의미 편집자 포함)
- 기존 약점을 반영한 개선안 제시
- 핵심 반전 인과 테이블 작성
- AI 실패 예측 + 가드레일 제안

#### 2-2. GPT 자문
GPT 5.4에게 story-consultant 평가 결과를 공유하고 추가 자문:
"이 재구축 계획이 원래 컨셉의 강점을 살리면서 약점을 해결하는가?"

> ✅ 완료 기준: story-consultant GO 판정. GPT 피드백은 참고 자료로 기록.

### Phase 3: 설정 재정립

#### 3-1. 기존 원고 아카이브
```bash
mv chapters chapters-archive
mkdir -p chapters/prologue chapters/arc-01
```
기존 원고는 `chapters-archive/`에 보존. 삭제하지 않는다.

#### 3-2. 설정 파일 재구성
Phase 1 보존 명세서를 항목별로 계승하며 재구성한다:
- `CLAUDE.md` — §5.1 의도적 비밀, §6 가드레일 포함
- `settings/01-style-guide.md` — 기존 문체 강점 보존, 약점 교정 규칙 추가
- `settings/02-episode-structure.md` — 에피소드 엔진 재설계
- `settings/03-characters.md` — 캐릭터 재설계 (기존 매력 보존 + 약점 보강)
- `settings/04-worldbuilding.md` — 설정 구멍 해결, Reader Onboarding 추가
- `settings/05-continuity.md` — lean 기준으로 갱신
- `settings/07-periodic.md` — 정기 점검 항목 설정
- `settings/08-illustration.md` — 일러스트 설정

기존 chapters-archive/를 참조하되, 설정 파일은 새로 작성한다.
**기존에서 잘 작동했던 요소(캐릭터 보이스, 세계관 규칙 등)는 명시적으로 보존한다.**

#### 3-3. 플롯 재설계
- `plot/master-outline.md` — 전체 아크 구성 재설계
- 첫 집필 구간의 `plot/{arc}.md` — prologue / arc-XX / epilogue / interlude 등 실제 시작 구간의 상세 비트시트
- `plot/foreshadowing.md` — 복선 계획

> ✅ 완료 기준: 모든 설정 파일 + plot 파일 작성 완료

### Phase 4: 사전 검증

#### 4-1a. /oag-check plan (동기 갭 — 먼저)
`plot/master-outline.md`와 첫 집필 구간의 `plot/{arc}.md`에 대해 oag-checker Planning Mode 실행.
PLANNING GAP / MOTIVATION GAP 발견 시 즉시 수정.

#### 4-1b. /why-check plan (설명 갭 — 4-1a 수정 후)
위 플롯에 대해 why-checker Planning Mode 실행.
PLANNING GAP 발견 시 즉시 수정.

#### 4-2. 교차 검증 (INIT-PROMPT 4단계와 동일)
팀 A (사실 관계), 팀 B (서사 실현성), 팀 C (표기/일관성) 검증.
모순 발견 시 즉시 수정.

#### 4-3. GPT 최종 검토
GPT에게 재구축된 설정 전체를 보여주고 최종 검토.

#### 4-4. 재검증 (조건부)
4단계 교차 검증에서 plot 파일이 수정되었다면, `/oag-check plan` + `/why-check plan`을 해당 파일에 대해 1회 재실행한다.

> ✅ 완료 기준: oag-check plan PASS + why-check plan PASS + 교차 검증 0건. GPT 검토 결과는 참고 기록.

### 승인 게이트 (Phase 3~4 결과)
설정 재구성 + 사전 검증 결과를 사용자에게 보고한다.
- 보존 명세서 준수 여부
- why-check plan 결과
- 교차 검증 결과
- GPT 검토 결과

**사용자 승인 후 Phase 5(초기화)로.** 이 시점 이후 summaries 리셋 + 보고서 삭제가 진행되므로 되돌리기 어렵다.

### Phase 5: summaries 초기화

기존 summaries/를 초기 상태로 리셋:
- `running-context.md` — "재집필 준비 상태"
- `episode-log.md` — 비우기
- `character-tracker.md` — 초기 상태
- `promise-tracker.md`, `knowledge-map.md`, `relationship-log.md` — 비우기
- `explained-concepts.md` — Reader Onboarding 미설명 추적 준비
- `decision-log.md` — 반복적 의도적 일탈 기록 준비
- `hanja-glossary.md`, `illustration-log.md`, `editor-feedback-log.md` — 비우기

기존 리뷰 보고서 삭제: `book-review.md`, `narrative-review-report.md`, `why-check-report.md` 등

> ✅ 완료 기준: summaries/ 전부 초기 상태, 기존 보고서 삭제

### Phase 6: batch-supervisor 설정

`batch-supervisor.md`에 변수 설정:
- `NOVEL_ID`, `SESSION`, `NOVEL_DIR`
- `ARC_MAP` (새 아크 구조에 맞게)
- `START_EP`, `END_EP`
- `CHUNK_SIZE` (-1 권장)

> ✅ 완료 기준: batch-supervisor 변수 전부 채워짐

### Phase 7: Git 커밋

```bash
cd no-title-{XXX}
git add -A
git commit -m "{소설명} 재구축 완료 — 설정 재정립, 기존 원고 아카이브"
```

> ✅ 완료 기준: 커밋 완료, chapters-archive/ 보존 확인

### Phase 8: 집필 시작 (Hybrid)

재구축이 완료되면 **Claude supervisor + Writer** 구조로 집필 (`writer_model`에 따라 Codex 또는 Claude):

```bash
cd /root/novel && claude
# → "no-title-{XXX}/batch-supervisor.md 대로 수행"
```

Claude supervisor가 tmux에서 Writer 세션을 실행하고 자동 관리한다.

---

## 아카이브 활용

`chapters-archive/`의 기존 원고는:
- 캐릭터 보이스 참고용 (이 캐릭터가 이런 식으로 말했었다)
- 좋았던 장면/대사 참고 (재활용하되 복붙 금지)
- 스타일 톤 참고
- 재집필 후 품질 비교용
- 아카이브에서 가져온 요소(캐릭터 보이스, 장면 패턴 등)는 settings 파일에 명시적으로 승격한 뒤 사용한다. 암묵적 참조 금지.

writer에게 "chapters-archive/의 기존 N화를 참고하되 새로 써라" 식으로 활용 가능.

---

## 주의사항

1. 재구축 ≠ 수정. 기존 원고를 고치는 것이 아니라 **처음부터 다시 쓰는 것**이다.
2. 핵심 컨셉은 바꾸지 않는다. 바꿔야 한다면 INIT-PROMPT로 새 프로젝트를 만들어라.
3. 기존 원고는 삭제하지 않는다. 언제든 비교/참고할 수 있어야 한다.
4. Phase 2(story-consultant)와 Phase 4(why-check plan)를 건너뛰지 마라. 재구축의 핵심 가치는 **사전 검증**이다.
5. **재구축 vs 신규 프로젝트의 경계**: 다음 중 하나라도 해당하면 REBUILD가 아니라 INIT-PROMPT로 새 프로젝트를 만들어라.
   - 주인공 교체
   - 장르 축 대변경 (예: 장르 A→장르 B)
   - 핵심 약속 2개 이상 변경
   - 에피소드 엔진 교체 (의뢰 루프→던전 루프 등)
```

---

## MIGRATION → REBUILD 연속 실행

마이그레이션 직후 재구축하려면:

```
1. MIGRATION-PROMPT.md 실행 (lean 구조 전환)
2. REBUILD-PROMPT.md 실행 (설정 재정립 + 재집필 준비)
3. batch-supervisor.md로 집필 시작
```
