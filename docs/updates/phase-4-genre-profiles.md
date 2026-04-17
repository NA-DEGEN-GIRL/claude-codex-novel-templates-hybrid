# Phase 4: Genre Profiles

**Status**: ✅ Completed (compile_brief branching deferred)
**Commit**: `e208f1c`

## Rationale

이 템플릿은 기본적으로 **무협(wuxia) 전제**가 강하게 박혀 있다. `CLAUDE.md §3.2.12`의 pre-modern numeral rules, `novel-hanja` MCP 기본 파이프라인, `settings/03-characters.md`의 객잔/하인 슬롯 등이 현대 로판/헌터물/게임판타지에서는 불필요하거나 noise로 작용한다.

Phase 4는 장르별 기본값을 **별도 profile 파일**로 분리하여, 프로젝트 초기화 시 해당 장르에 맞는 설정을 먼저 깔도록 한다. 이로써:
- 무협 기본값에 고정되어 있던 규칙이 장르 독립적으로 변경 가능
- 신규 사용자가 "이 장르에는 어떤 기본값이 적절한가" 참조 가능
- INIT-PROMPT가 장르 인자로 profile을 선택할 수 있는 경로 확보

**주의**: 이 phase는 **정적 문서 프리셋**만 제공. compile_brief.py의 profile 분기 로직 (동적 era 판정, hanja 파이프라인 토글)은 후속 작업으로 분리. 이유: compile_brief는 이미 `settings/04-worldbuilding.md`에서 era를 추출하므로 profile과 독립적으로 동작. 동적 분기는 drift 위험이 더 크고 테스트 부담이 커서 별도 phase로 분리하는 것이 안전.

## Changes

### 1. `settings/profiles/` 디렉토리 신설

6개 파일 생성:

| 파일 | 장르 | 주요 override |
|------|------|--------------|
| `README.md` | 인덱스 | profile 사용법, 지원 목록, 적용 원칙 |
| `wuxia.md` | 무협 (기본값) | 현재 템플릿 상태를 명시적으로 문서화 |
| `modern.md` | 현대 | Hanja OFF, 아라비아 허용, 표준 경어, 객잔→회사/학교 슬롯 |
| `game-fantasy.md` | 게임/헌터/시스템 | Hanja OFF, 아라비아 필수 (스탯), 시스템 창 표기 규칙 |
| `regression.md` | 회귀/환생/빙의 | POV 내면 예외 규칙, knowledge-map 이원 관리, **병용 profile 필요** |
| `romance.md` | 현대 로맨스 | 대화 위계 변화=이벤트, 1인칭 허용, 감정 세밀 묘사 |

각 profile 파일은 아래 구조로 일관:
- **적용 범위** — 이 profile이 맞는 장르 명시
- **기본값 (override 표)** — wuxia 기본값 대비 차이점 테이블
- **톤 기본값** — 장르별 권장 tone distribution
- **권장 Settings 변경** — settings/04-worldbuilding 등 필드 값 가이드
- **Writer/Reviewer 힌트** — 장르별 주의사항

### 2. `CLAUDE.md §1` — `profile:` 필드 추가

**Before**:
```yaml
- **illustration**: false
```

**After**:
```yaml
- **illustration**: false
- **profile**: wuxia  <!-- 장르 프리셋 (Phase 4). 값: wuxia | modern | game-fantasy | regression | romance. 상세: settings/profiles/README.md. -->
```

### 3. `CLAUDE.md §2 Folder Structure` — profiles/ 추가

```
│   ├── 08-illustration.md
│   └── profiles/               ← 장르 프리셋 (Phase 4): wuxia/modern/game-fantasy/regression/romance
```

## Rollback

### 전체 Phase 4 롤백
```bash
cd /root/novel/claude-codex-novel-templates-hybrid
git revert <phase-4-commit-sha>
```

### 부분 롤백

**profile 파일만 제거**:
```bash
rm -rf settings/profiles/
# CLAUDE.md §1에서 profile: 필드 제거
# CLAUDE.md §2에서 └── profiles/ 라인 제거
```

**CLAUDE.md 수정만 되돌리기**:
```bash
git checkout <pre-phase-4-sha> -- CLAUDE.md
# settings/profiles/는 남아도 무해 (참조만 안 하면 됨)
```

## Validation

```bash
cd /root/novel/claude-codex-novel-templates-hybrid

# 1. profiles 디렉토리 + 6개 파일 존재
ls settings/profiles/ | wc -l
# → 6 (README + 5 profiles)

ls settings/profiles/
# → README.md  game-fantasy.md  modern.md  regression.md  romance.md  wuxia.md

# 2. CLAUDE.md profile 필드 존재
grep -q "^- \*\*profile\*\*:" CLAUDE.md && echo OK

# 3. Folder Structure 업데이트
grep -q "└── profiles/" CLAUDE.md && echo OK

# 4. 각 profile 파일에 필수 섹션 존재
for f in wuxia modern game-fantasy regression romance; do
    grep -q "^## 적용 범위" settings/profiles/$f.md && echo "$f: OK"
done

# 5. 테스트 여전히 통과 (compile_brief는 profile 무관하게 동작)
python3 -m pytest tests/ 2>&1 | tail -3
# → 18 passed
```

## Dependencies

**선행**:
- Phase 0: Spec Canon (writer_model 등 정의됨) + docs 구조
- Phase 1~3: writer/reviewer 변경이 profile 문서가 참조하는 섹션과 일치

**후행**:
- **Phase 4.1 (follow-up)**: compile_brief.py의 profile-aware 분기 로직. 현재 `settings/04-worldbuilding.md`의 era만 읽음. profile이 활성화되면:
  - `profile: wuxia` → 기존 pre-modern 수사 규칙 유지
  - `profile: modern` → numeral notation rules를 modern으로 전환
  - `profile: game-fantasy` → system UI block 인식 규칙 추가
- Phase 5: drift 자동화에서 `profile: X`가 settings와 일치하는지 검증 (예: profile이 modern인데 settings/04에 pre-modern era가 있으면 warning)

## Known Issues / Follow-ups

1. **compile_brief.py profile 분기 미구현**: 가장 큰 follow-up. 현재 profile은 **정적 문서** 역할만 함. 동적 분기는 Phase 4.1 또는 Phase 5와 함께 구현. 우선순위: 중.
2. **profile 조합 관리**: `regression + wuxia` 같은 병용이 문서로만 안내됨. INIT-PROMPT 상에서 "regression을 선택하면 base profile을 하나 더 묻는" 로직 필요. 현재는 사용자 수동.
3. **각 profile의 깊이**: 현재 각 profile ~100줄. 깊은 장르 지식 (의료 로맨스 세부, 헌터물 레벨 밸런스 공식 등)은 포함 안 됨. 사용자 프로젝트별로 `settings/04-worldbuilding.md`에 추가로 상세화 필요.
4. **기본 seed 부재**: profile에 기본 조연 슬롯 이름, 샘플 대화, 샘플 scene이 없음. INIT-PROMPT가 profile을 받아 seed 내용을 생성해주는 것이 이상적. 현재는 placeholder만.
5. **profile이 없는 기존 프로젝트 migration**: 기존에 `profile:` 필드가 없던 프로젝트는 기본 `wuxia`로 간주 (현재 기본값과 일치). 명시적 migration은 불필요하나, CLAUDE.md §1에 필드 추가 권장.
6. **`settings/06-humor-guide.md`는 profile 무관하게 optional**로 유지. profile별 humor 기본값이 있을 수 있음 (romance: 가벼운 유머 3, game-fantasy: 사이다 5) — 향후 각 profile에 `humor_density` 필드 추가 여지.

## References

- 원 리뷰: general-purpose agent의 "장르 호환성" 지적 (무협 전제가 강하게 박힘, 템플릿이 범용이 아님)
- 영향 파일: `settings/profiles/` (신규 디렉토리 + 6 파일), `CLAUDE.md`
