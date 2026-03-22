GPT 5.4로 소설을 독자 관점에서 리뷰한다. Claude가 오케스트레이션하고, GPT가 읽고 평가한다.

## 사용법

`/book-review-gpt`

## 왜 GPT로?

Claude book-review와 다른 관점을 제공한다. 두 리뷰를 비교하면 균형 잡힌 평가가 된다.

## 실행 절차

### Step 1: 아크 구조 파악

chapters/ 폴더에서 아크별 에피소드 파일을 수집한다.

- 각 아크의 문자 수를 확인
- **아크가 80,000자를 초과하면 반으로 분할** (서사 경계에서 끊기)
- 소설의 아크 구조(prologue, arc-01, arc-02...)를 기준으로 분할

### Step 2: 순차 아크 리뷰 (GPT 5.4)

**반드시 순차 실행한다. 병렬 금지.** 이전 아크의 구조화된 요약이 다음 아크의 맥락이 되므로.

각 아크에 대해:

```bash
CONTENT=$(cat chapters/{arc}/*.md)

codex exec -m gpt-5.4 "
You are reviewing a Korean novel arc by arc. This is ARC {N} ({arc_name}, episodes {start}-{end}).

## Previous arcs (structured carry-forward):
${CARRY_FORWARD}

## Instructions:
Read the text below as a READER. After reading, provide ALL of the following.
Every finding MUST cite a specific episode number.

### 1. 아크 요약 (3-4문장)

### 2. 구조화된 상태 기록 (다음 아크에 전달됨)
- 핵심 캐릭터 현재 상태 (이름: 상황 1줄씩)
- 미해결 갈등/미스터리
- 주요 관계 변화
- 이 아크에서 설치된 복선

### 3. 읽다가 걸린 순간 (화수 명시)
읽다가 \"뭐야 이게?\", \"갑자기 왜?\", \"이야기를 따라가고 싶은 마음이 깨졌다\"고 느낀 순간. 특히:
- \"왜 이 캐릭터가 이걸 했지?\" (동기 미설명)
- \"이게 어떻게 가능하지?\" (방법 미설명)
- \"이 사람이 왜 이걸 몰랐지?\" (능력자의 탐색 실패)
- \"아까는 내일이라더니 지금은 먼 미래?\" (시간 모순)
이유를 분석하지 말고, 어디서 무엇이 이상했는지 나열.

### 4. 읽다가 빨라진 순간 (화수 명시)
몰입이 올라간 구간.

### 5. 읽다가 느려진 순간 (화수 명시)
지루하거나 건너뛰고 싶었던 구간.

### 6. 캐릭터 일관성
이전 아크와 비교해 캐릭터 행동/말투에 변화가 있었는가? 자연스러운 변화인가 급변인가?

### 7. 아크 점수 (/10)
점수 기준: 7=괜찮음, 8=좋음, 9=매우 좋음, 10=걸작. 6 이하는 명확한 결함이 있을 때만.

### 8. 가장 인상적인 대사 1개 (정확히 인용)

Write in Korean. Be honest and specific.

---
${CONTENT}
"
```

**Carry-forward 규칙**:
- 첫 아크: carry-forward 없이 실행
- 이후 아크: **이전 아크의 "구조화된 상태 기록"을 전부 누적**하여 전달
- 누적이므로 후반 아크도 초반 캐릭터/복선 정보를 유지할 수 있음
- 마지막 아크: 추가로 "9. 끝나고 남은 감정", "10. 초반에 약속한 소설과 후반의 실제 소설이 같은 작품처럼 느껴졌는가?" 요청

### Step 3: 통합 리뷰 (GPT 5.4)

모든 아크 리뷰를 모아서 GPT 5.4에 최종 통합 리뷰를 요청한다:

```bash
codex exec -m gpt-5.4 "
You reviewed the Korean novel '{title}' ({total_eps} episodes) arc by arc.
Here are ALL your arc reviews. Now write a UNIFIED book review in Korean.

{아크별 리뷰 전부}

IMPORTANT: The first 5 sections MUST use EXACTLY these markdown headings (with emoji, NO numbering prefix). A web reader parses these exact patterns:

## 📖 한줄 소개
(한 문장으로 소설의 읽는 경험을 전달)

## ⭐ 점수: {N}/10

## 🎯 이런 사람에게 추천
(3개 bullet points)

## ⛔ 이런 사람은 비추
(2개 bullet points)

## 💬 한마디
(감정적 독후감 한 문장. 이 줄이 reader에서 대표 인용문으로 표시됨)

SPOILER RULES for the 5 sections above (📖/⭐/🎯/⛔/💬):
- These are shown to POTENTIAL READERS who have NOT read the novel.
- ONLY mention: genre, tone, prose style, emotional texture, early-arc setup.
- Do NOT reveal: plot twists, identity reveals, character deaths, relationship outcomes, ending details, or mid/late-story events.
- Do NOT use: 마지막, 결말, 엔딩, 반전, 정체, 드러난다, 밝혀진다, 사실은, 알고 보니
- Do NOT quote specific lines from the novel in these sections.
- Bad: '주인공이 사라진다', '반전이 세 겹', '마지막 문장이 첫 문장을 뒤집는다'
- Good: '건조한 문체가 서서히 온기를 머금는 작품', '억눌린 감정이 오래 남는다'
- 🎯/⛔: Describe reader preferences only (pace, tone, genre taste). No plot hints.
- Sections AFTER 💬 (총평, 강점/약점 등) are author-only — spoilers and quotes OK there.

Then continue with:
5. 총평 (3문장)
6. 아크별 점수 테이블
7. 강점 top 3 (반드시 화수 + 정확한 인용 포함)
8. 약점 top 3 (반드시 화수 명시)
9. 읽다가 걸린 순간 vs 빨라진 순간 (전체 통합, 화수 명시)
10. 비교 작품
11. 가장 크게 거슬린 문제 1개 (화수 + 구체적 설명)
12. 점수 자기 검증: 아크별 감정과 종합 점수가 일치하는가?

Write entirely in Korean. Be honest, specific, quote memorable lines.
Do NOT inflate scores. 8/10 is already a good novel.
"
```

### Step 4: 저장

결과를 `summaries/book-review-gpt.md`에 저장한다.

구성:
1. 통합 리뷰 (Step 3 결과)
2. 아크별 상세 리뷰 (Step 2 각 결과)

## 주의

- settings/, plot/, summaries/는 GPT에 보내지 않는다. 본문만.
- carry-forward는 GPT가 직접 쓴 구조화된 상태 기록만 사용 (Claude가 요약/편집하지 않음)
- codex exec 호출이 실패하면 재시도 1회. 2회 실패 시 해당 아크를 건너뛰고 다음으로 진행하되, 로그에 기록.
- 점수 보정: GPT는 Claude보다 관대한 경향이 있음. 통합 리뷰에 "점수 자기 검증" 항목을 포함하여 인지하게 한다.
