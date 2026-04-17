# Phase 7: Profile + WRITER-HOLD Runtime

**Status**: ✅ Completed
**Commit**: (추가 후 기록)

## Rationale

Phase 2/4의 핵심 메커니즘 4개가 런타임에서 작동하지 않던 문제를 해결:

1. **`[WRITER-HOLD: 사유]` 태그 생성 경로 부재** (Phase 2): writer prompt 어디에도 생성 절차 없었음. "면책 조항은 있으나 아무도 안 쓰는" 상태.
2. **§5.1A Intentional Style Deviations 표가 빈 상태** (Phase 2): 신규 프로젝트는 `{{STYLE_DEV_1}}` placeholder뿐. 초반 5~10화가 voice preservation 가장 취약한 시기인데 보호 못 함.
3. **profile 필드 런타임 무시** (Phase 4): `profile: modern` 설정해도 compile_brief / writer / reviewer 어디에도 참조 없음. 장식에 가까운 필드.
4. **regression profile 병용 UX 공백** (Phase 4): "wuxia + regression 병용 필요"라면서 CLAUDE.md §1 profile이 단일값 제약. syntax 부재.
5. **settings/03-characters.md 생활 조연 슬롯 무협 고정**: profile: modern 선언해도 "객잔/제자" 슬롯이 그대로.

Phase 7은 위 4개의 **운영 경로**를 명시적으로 문서화하여 "문서만 존재"를 "실행 가능한 절차"로 전환.

## Changes

### A. INIT-PROMPT.md — profile 선택 분기 추가

**프롬프트 1 조건 리스트**에 `profile` 필드 추가:
```
- **profile**: [wuxia / modern / game-fantasy / romance / regression+{base}]
```

**3단계 프로젝트 생성**에 새 단계 0 추가:
```
0. Profile 결정: 사용자가 명시한 profile 값을 그대로 사용하거나,
   장르 자동 매핑 (무협→wuxia, 현대→modern, 헌터→game-fantasy, 로맨스→romance,
   회귀→regression+{base}). 선택된 profile의 settings/profiles/{profile}.md를 읽고
   아래 단계에서 값 override 시 참조.
```

**3단계 4번, 5번 수정**:
- 4번: CLAUDE.md의 `profile:` 필드를 0단계 값으로 설정. §5.1A 표에 해당 profile의 seed 3~5행을 `settings/profiles/{profile}.md`에서 복사.
- 5번: "Profile 기반 override 필수". 04-worldbuilding의 era/units/currency, 03-characters의 생활 조연 슬롯을 profile에 맞게 실제 값으로 교체. 무협이 아니면 hanja 섹션 삭제.

### B. `[WRITER-HOLD]` 태그 생성 경로 명시

`.claude/prompts/claude-fixer.md` / `codex-fixer.md` 두 파일에 **"Writer Dissent — fix-spec 거부 경로"** 블록 추가:

1. Writer가 fix-spec의 특정 FIX 항목을 Voice Profile / 캐릭터 시그니처 훼손으로 판단 → 해당 FIX만 수정하지 않음.
2. 변경 요약에 `[WRITER-HOLD] FIX-{번호} | 원 표현: "X" | 사유: "..."` 형식으로 보고.
3. Review 세션이 FIX_DONE 감지 후 HOLD 줄을 파싱하여 `summaries/style-lexicon.md`에 `| X → (교정 거부) | [WRITER-HOLD] 사유 |` append.
4. 이후 리뷰에서 공통 면책 5종 중 #2(style-lexicon WRITER-HOLD)에 의해 자동 면책.
5. 같은 표현 3회+ HOLD 누적 시 supervisor가 §5.1A 정식 승격 제안.

**제약**: WRITER-HOLD는 style/voice/naturalness/repetition fix에만 허용. 사실관계/연속성/금지사항(§5) fix는 거부 불가.

### C. §5.1A profile별 seed 제공 (5 profile)

각 `settings/profiles/{profile}.md`에 "§5.1A Intentional Style Deviations — {profile} seed" 섹션 추가. 3~4 rows per profile.

**wuxia seed**: 전투 단문 급증 / 무공명 반복 / 판단성 마감문 / 한자 30화 룰 예외
**modern seed**: 내면 구어체 / 외래어 빈도 / 짧은 대화 교환 / 감정 직서술 부분 허용
**game-fantasy seed**: 시스템 창 정확 수치 / 스킬명 반복 / 캐주얼+위기 교차 / 시스템 음성 무감정체
**romance seed**: 관계 정점 여운형 / 내면 메타적 자기 분석 / 호칭 변화 반복 / 신체 반응 시그니처
**regression seed**: POV 현대 어휘 / 기시감·예지 선언 / 감정 대신 냉소 (base와 병합)

INIT-PROMPT 3단계 4번에서 해당 seed를 CLAUDE.md §5.1A로 복사 지시.

### D. regression profile 병용 UX 명확화

**`profile:` syntax 3가지**:
| Syntax | 의미 |
|--------|------|
| 단일 (`wuxia` / `modern` / `game-fantasy` / `romance`) | 해당 profile 단독 적용 |
| **`regression+{base}`** | regression override + base profile |
| 혼합 장르 | 단일 + §1.2 Thematic Statement 명시 |

**병용 적용 순서**: base profile 전체 적용 → regression Override 추가 → §5.1A seed 병합 (중복 시 regression 우선).

**문서 반영**:
- `settings/profiles/README.md`: "Profile syntax" 표 + "병용 Profile 적용 순서" 추가
- `settings/profiles/regression.md`: "⚠️ 병용 Profile" 섹션에 `regression+{base}` syntax 명시
- `CLAUDE.md §1 profile` 주석: "`wuxia | modern | game-fantasy | romance | regression+{base}`" 명시

**CLAUDE.md profile 주석에 런타임 제약 명시**: "compile_brief/writer/reviewer가 이 필드를 자동 읽지 않는다 (Phase 4.1로 연기). INIT-PROMPT 3단계 0번이 profile 값을 보고 settings/ 파일을 수동으로 맞춤". 사용자 오해 방지.

### E. settings/03-characters.md 생활 조연 슬롯 profile-aware

**Before**: `소속 내부 제자/하인`, `객잔/숙소 인물` 등 **무협 고정** 5개 슬롯.

**After**: 각 profile별 5개 슬롯 목록:
- **wuxia**: 제자/하인, 상급자 보조, 객잔, 치료, 이동 동선 (기존)
- **modern**: 직장 동료, 가족, 이웃/생활권, 친구, 클라이언트
- **game-fantasy**: 길드 동료, NPC/상점, 라이벌, 관리자, 조력자/멘토
- **romance**: 친구, 상대역 친구/동료, 라이벌/삼각, 가족, 생활권 인물
- **regression+{base}**: base의 슬롯 + 회귀 전후 관계 변화 보조 인물 1명

INIT-PROMPT 3단계 5번에서 profile에 맞게 슬롯 교체.

## Rollback

### 전체 Phase 7 롤백
```bash
git revert <phase-7-commit-sha>
```

### 부분 롤백

**WRITER-HOLD 경로만 제거** (fixer 프롬프트):
```bash
git checkout <pre-phase-7-sha> -- .claude/prompts/claude-fixer.md .claude/prompts/codex-fixer.md
```

**§5.1A seed만 제거** (profile 파일):
```bash
git checkout <pre-phase-7-sha> -- settings/profiles/wuxia.md settings/profiles/modern.md settings/profiles/game-fantasy.md settings/profiles/romance.md settings/profiles/regression.md
```

**INIT-PROMPT의 profile 분기 제거**:
```bash
git checkout <pre-phase-7-sha> -- INIT-PROMPT.md
```

**03-characters 슬롯 원복**:
```bash
git checkout <pre-phase-7-sha> -- settings/03-characters.md
```

## Validation

```bash
cd /root/novel/claude-codex-novel-templates-hybrid

# 1. INIT-PROMPT에 profile 분기 추가 확인
grep -n "Profile 결정 (Phase 7" INIT-PROMPT.md

# 2. WRITER-HOLD 경로 확인
grep -l "WRITER-HOLD" .claude/prompts/claude-fixer.md .claude/prompts/codex-fixer.md

# 3. 5개 profile 모두 §5.1A seed 포함
for p in wuxia modern game-fantasy romance regression; do
  grep -c "§5.1A Intentional Style Deviations" settings/profiles/$p.md
done
# → 모두 1

# 4. regression syntax 명시
grep "regression+{base}" settings/profiles/regression.md settings/profiles/README.md CLAUDE.md

# 5. 03-characters profile별 슬롯 존재
grep "^\*\*modern\*\*\|^\*\*game-fantasy\*\*\|^\*\*romance\*\*" settings/03-characters.md

# 6. 테스트 통과
python3 -m pytest tests/ 2>&1 | tail -3
# → 18 passed

# 7. validate-docs
python3 scripts/validate-docs.py 2>&1 | tail -3
# → baseline WARN 2~3건
```

## Dependencies

**선행**:
- Phase 0~6: 모두 완료. 특히 Phase 6의 공통 5종 면책 통일이 WRITER-HOLD 경로(면책 #2)의 기반.

**후행 (Phase 4.1로 연기된 작업)**:
- **compile_brief.py의 profile-aware 분기**: 현재는 INIT-PROMPT가 settings 파일을 수동 override. 런타임에서 profile 값을 읽어 동적으로 brief 생성 포맷을 조정하는 작업은 별도 phase 필요.
- **validate-docs.py의 WRITER-HOLD 추적 check**: style-lexicon.md의 [WRITER-HOLD] 태그 수를 세서 3회+ 누적 시 §5.1A 승격 알림 — Phase 8에서 추가.

## Known Issues / Follow-ups

1. **WRITER-HOLD 파싱 구현은 review 세션 LLM 지시**: 실제 Python 파서가 없고, review 세션이 변경 요약을 읽어 style-lexicon에 append하는 것. LLM이 놓치면 drift. `scripts/`에 `extract-writer-holds.py` 파서 추가 권장 (향후).
2. **§5.1A seed가 CLAUDE.md에 자동 주입되지 않음**: INIT-PROMPT 지시에 의존. INIT-PROMPT를 따라간 Claude가 seed 복사를 실수하면 빈 표. validate-docs가 "profile 설정됐는데 §5.1A 비어있음" 체크로 탐지 가능 (Phase 8).
3. **regression+{base} syntax 파싱 규칙**: `profile: regression+wuxia` 값을 validate-docs가 legal로 받아들일지 unknown. Phase 8에서 파싱 규칙 추가 필요.
4. **생활 조연 슬롯 profile별 구성**이 기본 5개 기준으로만 제공. "스릴러 프로젝트는 어떤 슬롯이 적절?", "의학 드라마는?" 등 세부 장르 미커버.
5. **WRITER-HOLD 제약 (style 범주만)**이 LLM 주관 판단. "이건 style인가 사실관계인가?" 애매한 경우 writer가 HOLD 오용 가능. 첫 몇 번은 사용자가 검토 필요.
6. **INIT-PROMPT의 "자동 매핑"** ("무협→wuxia" 등)이 장르 서술 다양성을 감당 못 할 수 있음. "팩션 SF 회귀" 같은 변주에서 LLM이 어떤 profile을 고를지 예측 불가. 수동 명시 권장.
7. **`profile:` 필드 값 검증 없음**: `profile: xyz-random`을 넣어도 어디서도 에러 안 남. Phase 8 validate-docs에 추가 예정.

## References

- 원 리뷰 (5-agent) Tier 0: Phase 2 4대 메커니즘 런타임 공백, Phase 4 profile no-op
- 영향 파일: `INIT-PROMPT.md`, `.claude/prompts/claude-fixer.md`, `.claude/prompts/codex-fixer.md`, `settings/profiles/*.md` (5개), `settings/profiles/README.md`, `settings/profiles/regression.md`, `settings/03-characters.md`, `CLAUDE.md`
