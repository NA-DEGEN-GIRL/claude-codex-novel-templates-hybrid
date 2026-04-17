# Template Updates Log

이 디렉토리는 템플릿에 가해진 구조적 변경을 기록한다. 각 phase 파일은 **무엇을, 왜, 어떻게 되돌릴 수 있는지**를 담는다.

## 목적

- **롤백 용이성**: 각 phase는 독립적으로 git revert 또는 수동 rollback 가능
- **재검토 용이성**: 어떤 결정이 어떤 근거로 내려졌는지 추적
- **점진적 개선**: 다음 개선자가 이 로그를 읽고 추가 작업 지점 파악

## Phase 색인

| Phase | 주제 | 상태 | 파일 |
|-------|------|------|------|
| 0 | Cleanup & reorg | ✅ | [phase-0-cleanup.md](phase-0-cleanup.md) |
| 1 | Hot path optimization | ✅ | [phase-1-hot-path.md](phase-1-hot-path.md) |
| 2 | Voice preservation | ✅ | [phase-2-voice-preservation.md](phase-2-voice-preservation.md) |
| 3 | Role consolidation | ✅ | [phase-3-role-consolidation.md](phase-3-role-consolidation.md) |
| 4 | Genre profiles | 🔄 | [phase-4-genre-profiles.md](phase-4-genre-profiles.md) |
| 5 | Drift automation | ⏳ | [phase-5-drift-automation.md](phase-5-drift-automation.md) |

**범례**: ✅ 완료 · 🔄 진행중 · ⏳ 대기

## 각 Phase 문서 포맷

모든 phase 문서는 아래 구조를 따른다.

```markdown
# Phase N: 제목

## Rationale
왜 이 변경이 필요한가. 근거(원 리뷰 결과 참조).

## Changes
파일별 변경 내역. 각 항목에:
- 파일 경로
- 변경 전/후 요약
- 의도

## Rollback
이 phase를 되돌리는 방법:
1. git revert <commit-sha>  또는
2. 수동 rollback 단계

## Validation
변경 후 확인 방법 (스모크 테스트, 로그 확인 등).

## Dependencies
이 phase를 적용하기 전에 선행되어야 할 phase.

## Known Issues / Follow-ups
남은 이슈와 다음 개선 지점.
```

## 롤백 전략

### 전체 롤백 (모든 phase)
```bash
# 첫 번째 phase 시작 직전 커밋 확인
git log --oneline | grep -B1 "Phase 0"

# 해당 지점으로 리셋 (주의: 이후 커밋 손실)
git reset --hard <pre-phase-0-sha>
```

### 특정 phase만 롤백
```bash
# 해당 phase의 커밋 sha 확인 (phase 문서 하단에 기록)
# revert
git revert <phase-N-sha>

# 또는 phase 문서의 "Rollback" 섹션의 수동 단계 따라가기
```

### Phase를 부분 수정
해당 phase 문서의 "Changes" 섹션에서 파일별 변경 내역을 보고, 원하는 부분만 편집 후 재커밋.

## 주의사항

- **phase 간 의존성 존중**: Phase 1은 Phase 0에 의존하지 않지만, Phase 3은 Phase 1의 writer prompt 구조를 전제로 함. 각 phase 문서 "Dependencies" 섹션 확인.
- **commit 단위는 phase 단위**: 한 phase는 여러 파일 변경을 담아도 한 커밋으로 묶음. revert 단순화.
- **template 사용자에게 영향 있는 변경은 CHANGELOG.md에도 반영**: update log는 개발자/유지보수자용, CHANGELOG는 사용자용.
