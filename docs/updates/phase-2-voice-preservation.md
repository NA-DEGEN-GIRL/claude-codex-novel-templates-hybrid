# Phase 2: Voice Preservation

**Status**: ✅ Completed
**Commit**: (추가 후 기록)

## Rationale

이 템플릿의 가장 큰 구조적 결함은 **평탄화(flattening)**다. 매 화 5~6종 외부 AI 피드백(gemini/nim/gpt/ollama/proxy/gpt-naturalness)이 동일 방향의 "매끈한 표준 한국어"로 수렴시키고, hybrid에서는 codex writer를 claude reviewer가 매 화 깎아내 작가 개성이 누적적으로 유실된다.

`docs/archive/style-flexibility-proposal.md`가 별도 문서로 존재한다는 사실 자체가 저자들도 이 문제를 인지한다는 증거. Phase 2는 해당 제안을 **정식 적용**한다.

핵심 3가지:
1. **External feedback 기본값을 보수적으로**: gemini/nim 기본 ON → OFF. proxy만 기본 ON(한국어 line-edit이라 저비용).
2. **Writer dissent 경로 신설**: reviewer의 style 지적을 writer가 거부할 수 있는 공식 경로. `§5.1A Intentional Style Deviations` + `style-lexicon [WRITER-HOLD]` 태그.
3. **Reviewer 편향 교정**: AI Psychological Suspicion Patterns의 "발견 즉시 감점" → "발견 → 맥락 확인 → 미정당 + 정량 트리거 초과 시 감점". P3/P5/P10에 정량 트리거 추가.

## Changes

### 1. `CLAUDE.md §1` — External feedback 기본값 변경

**Before**:
```yaml
gemini_feedback: true      # 기본 ON
nim_feedback: true         # 기본 ON
ollama_feedback: false
gpt_feedback: false
proxy_feedback: false      # 기본 OFF
```

**After**:
```yaml
gemini_feedback: false     # 기본 OFF (평탄화 방지)
nim_feedback: false        # 기본 OFF
ollama_feedback: false
gpt_feedback: false
proxy_feedback: true       # 기본 ON (한국어 line-edit — 저비용/저지연)
```

추가: §1 defaults 아래에 "External feedback 운영 원칙" 블록 신설 — 매 화 6종을 돌리면 작가 개성이 평균으로 수렴한다는 점, proxy만 기본 ON인 이유, 아크 경계/교차검증 시 opt-in 권장.

### 2. `CLAUDE.md §5.1A` — Intentional Style Deviations 신설

§5.1 Intentional Mysteries 직후 §5.1A 추가. 표 포맷:

```markdown
| 항목 | 적용 범위 | 허용 변화 | 서사적 이유 |
|------|----------|----------|-----------|
| {{STYLE_DEV_1}} | {{아크/화수/장면}} | {{예: 단문 급증, 비유 밀도 상승, 반복어 허용, 번역투 풍자}} | {{왜 필요한가}} |
```

판정 원칙:
- 등록 없는 변화는 드리프트 의심 신호
- 등록된 변화라도 장면 기능이 약하면 면책 안됨
- 장면 종료 후 기본 보이스 복귀

**Writer dissent 경로**: reviewer 지적 거부 시 `summaries/style-lexicon.md`에 `[WRITER-HOLD: 사유]` 태그로 등록 → 이후 자동 면책. 3회 이상 누적 시 §5.1A 표로 정식 승격.

### 3. `.claude/agents/unified-reviewer.md` L9 — "한국어 결합 자연성" 판정 범위 축소

**Before**:
> 단, **한국어 결합 자연성은 예외 없이 본다**. 보이스처럼 보이더라도 주어-서술어, 명사-동사, 추상명사-행위 결합이 한국어에서 부자연스러우면 지적한다.

**After** (새 블록 "한국어 결합 자연성 판정 범위"):
- §0.5 평균체 회피, 명백한 번역투, 이해 불가 결합에 한정
- AI 습관 패턴과 작가 시그니처 구별
- 자동 면책 3종: §5.1A 등록, style-lexicon 등록, §0.5 허용 이탈 유형 장면 변주

### 4. `.claude/agents/unified-reviewer.md` — Same-Model Note 수정

**Before**: (1) Gemini/GPT 외부 피드백 "standard/full에서 더 강하게 반영", (2) P3/P5/P8/P9 추가 주의, (3) 애매하면 ⚠️ 기본.

**After**:
- (1) 외부 피드백을 **필요 시 opt-in** (매 화 상시 아님)
- (2) P3/P5/P10에 주의 + **발견 → 맥락 확인 → 미정당 시에만 감점** (즉시 감점 아님)
- (3) 애매하면 "⚠️ 플래그"가 아니라 **"통과 or Voice Profile 근거 명시"** 택일

### 5. `.claude/agents/unified-reviewer.md` — AI Psychological Suspicion Patterns 재설계

**Before**: 10개 패턴, "Pattern found → justification check → unjustified면 감점" — 사실상 일단 플래그 편향.

**After**: 판정 순서 명시 ("발견 → 맥락 확인 → 미정당일 때만 감점"). 표에 **정량 트리거 컬럼** 추가:
- P3 메타적 자기 분석: 장편 3회 이상 연속 / 한 화 4회 이상에서만 플래그. 1~2회는 캐릭터 특성.
- P5 감정 선언: 한 화 3회 이상 / 주요 감정 장면 반복에서만 플래그. 1~2회는 허용.
- P10 증거 없는 성장: 장편 3화 이상 연속 누적 선언일 때만 플래그. 1회는 복선.
- P1/P2/P4/P6/P7/P8/P9: 1회 발견 시 맥락 확인 (변화 없음, 원래 맥락 확인 전제).

**면책 우선 순위 4단계** 명시: (1) §5.1A 등록, (2) style-lexicon [WRITER-HOLD], (3) 03-characters 대표 대사 등록, (4) 없으면 트리거 확인.

### 6. `.claude/agents/narrative-fixer.md` — Required Context + Step 1 확장

**Required Context**에 추가:
- 3번 항목에 "**§5.1A Intentional Style Deviations**" 명시
- 4번 항목에 "§0.5 허용 이탈 유형 and §0.7 피해야 할 평균체" 명시
- 신규 9번 항목: `summaries/style-lexicon.md` 로딩 (WRITER-HOLD 태그 자동 면책)

**Step 1 Analyze**에 "**Override check**" 블록 추가: style/voice/naturalness/repetition 성격 진단이면 §5.1A / style-lexicon / §0.5 허용 이탈 유형 셋 중 하나 매칭 시 fix-spec에 `[SKIP: override matched — {근거}]` 기록, 수정 안 함.

### 7. `.claude/agents/korean-naturalness.md` — 반평탄화 안전장치 추가

원칙 섹션 뒤에 **"### 반평탄화 안전장치"** 블록 신설:
- **면책 우선 체크 3종**: §5.1A / style-lexicon / §0.5 허용 이탈 유형
- **보수적 운영 원칙**: 한 번 스침 플래그 금지, 반복/독해 마찰 시에만 승격, 낯섦 ≠ 오류, 고전/서정/압축 보이스는 더 넓은 허용폭.

### 8. `.claude/agents/repetition-checker.md` — 면책 우선 체크 추가

원칙 섹션에 "**면책 우선 체크 (Phase 2)**" 블록 추가:
- §5.1A Intentional Style Deviations
- style-lexicon `[WRITER-HOLD]`
- decision-log 의도적 반복
- 03-characters "대표 대사" 시그니처
- 관계 정점 장면의 교환 패턴

## Rollback

### 전체 Phase 2 롤백
```bash
cd /root/novel/claude-codex-novel-templates-hybrid
git revert <phase-2-commit-sha>
```

### 부분 롤백

**External feedback 기본값만 되돌리기**: `CLAUDE.md §1` 섹션을 이전 값으로 수정 (gemini/nim을 true로, proxy를 false로). 또는:
```bash
git show <pre-phase-2-sha>:CLAUDE.md | sed -n '25,35p'  # 원본 값 확인
# 그 값으로 현재 파일 수정
```

**§5.1A 제거**: `CLAUDE.md`에서 §5.1A 블록 전체 삭제. 의존: narrative-fixer / unified-reviewer / korean-naturalness / repetition-checker의 "§5.1A 참조" 구문도 제거 필요.

**unified-reviewer 편향 복원**: `git checkout <pre-phase-2-sha> -- .claude/agents/unified-reviewer.md`

**개별 에이전트 복원**:
```bash
git checkout <pre-phase-2-sha> -- .claude/agents/narrative-fixer.md
git checkout <pre-phase-2-sha> -- .claude/agents/korean-naturalness.md
git checkout <pre-phase-2-sha> -- .claude/agents/repetition-checker.md
```

## Validation

```bash
cd /root/novel/claude-codex-novel-templates-hybrid

# 1. CLAUDE.md 기본값 확인
grep -E "gemini_feedback|nim_feedback|proxy_feedback" CLAUDE.md | head -3
# → gemini_feedback: false / nim_feedback: false / proxy_feedback: true

# 2. §5.1A 존재 확인
grep -q "5.1A Intentional Style Deviations" CLAUDE.md && echo OK

# 3. unified-reviewer 정량 트리거 확인
grep -A1 "P3 | 메타적 자기 분석" .claude/agents/unified-reviewer.md | grep "3회 이상" && echo OK
grep "발견 → 맥락 확인" .claude/agents/unified-reviewer.md && echo OK

# 4. narrative-fixer Override check 확인
grep -q "Override check (Phase 2 voice preservation)" .claude/agents/narrative-fixer.md && echo OK

# 5. korean-naturalness 반평탄화 안전장치 확인
grep -q "반평탄화 안전장치" .claude/agents/korean-naturalness.md && echo OK

# 6. repetition-checker 면책 우선 체크 확인
grep -q "면책 우선 체크 (Phase 2" .claude/agents/repetition-checker.md && echo OK

# 7. 테스트 여전히 통과
python3 -m pytest tests/ 2>&1 | tail -3
# → 18 passed
```

## Dependencies

**선행**:
- Phase 0: Spec Canon + docs/archive (style-flexibility-proposal를 여기서 참조)
- Phase 1: writer prompt diet (이 phase에서 WRITER dissent 경로의 "writer" 동작 정의가 간결한 상태라 용이)

**후행**:
- Phase 3: narrative-fixer Role 재정의 시 이 phase의 Override check 블록이 유지되도록 주의
- Phase 4: 장르 프리셋 설계 시 각 프로필이 style-lexicon/§5.1A 기본 seed를 제공하면 더 유용

## Known Issues / Follow-ups

1. **`[WRITER-HOLD]` 태그의 writer 측 실행**: 현재는 writer prompt에 "거부 시 style-lexicon에 등록" 명시가 없음. Phase 3 narrative-fixer 재정의 시 writer prompt에도 "fix-spec 거부 시 style-lexicon에 `[WRITER-HOLD: 사유]` append" 절차 추가 필요.
2. **정량 트리거 검증**: P3 "장편 3회 이상" 같은 정량 조건을 reviewer가 실제로 계산 가능한 컨텍스트를 받는지는 compile_brief 출력에 의존. 현재는 episode-log의 최근 화만 brief에 포함 — 장편 추적이 부족할 수 있음. 별도 확인 필요.
3. **§5.1A 표가 비어 있는 신규 프로젝트**: seed 항목 없이 "{{STYLE_DEV_1}}" placeholder만 남음. INIT-PROMPT에서 장르에 따라 기본 seed를 제안하는 로직 필요 (Phase 4 genre profile과 연계).
4. **proxy_feedback 의존성**: 로컬 LLM 프록시가 설치되지 않은 환경에서 기본값 true는 "empty feedback" 상태 반복. 설치 안내를 README와 CLAUDE.md에 명시해야 함 (Phase 0에서 부분 처리, Phase 5 drift 자동화에서 최종 검증).
5. **unified-reviewer의 기존 외부 피드백 처리 로직 (L158~)**은 CLAUDE.md의 flags를 읽어 동작하므로 기본값 변경만으로 충분. 단, D 섹션 (External Feedback Processing)의 "매 화" 문구가 "flag가 true인 경우 매 화"로 읽히게 문구 다듬을 필요가 있음 — 후속 마이크로 조정.

## References

- 원 리뷰: general-purpose agent의 "리뷰 문화 / 과잉 감사" + prompt-engineer의 "AI Psychological Suspicion Patterns P1-P10 편향"
- 적용 문서: `docs/archive/style-flexibility-proposal.md` (archive 위치의 제안서를 정식 적용)
- 영향 파일: `CLAUDE.md`, `.claude/agents/unified-reviewer.md`, `.claude/agents/narrative-fixer.md`, `.claude/agents/korean-naturalness.md`, `.claude/agents/repetition-checker.md`
