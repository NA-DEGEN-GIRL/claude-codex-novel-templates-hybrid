# Phase 9: 4-Lens Audit Fixes (전달·실행·반영 체인 수리)

**Status**: ✅ Completed
**Date**: 2026-07-02
**근거 감사**: `/root/novel/hybrid-template-audit-2026-07-02.md` (4개 렌즈 병렬 감사 — 한글/문체, 맥락 체인, 검증망, 실증)

## Rationale

운영자가 관찰한 4대 실패 모드(① 이상한 한글 표현 ② 어색한 문체 ③ 맥락 망각 ④ 존댓말/반말 오류)를 4개 렌즈로 감사한 결과, 지배적 원인은 규칙 부족이 아니라 **전달·실행·반영 체인 단절**로 확인됨:

- **전달**: 개선판 compile_brief가 MCP에서 서빙되지 않음(구버전 이원화), style-guide §4/§6 예문이 writer 미도달, §8.2/8.3·기본값·"현재 대화 모드"가 파서 추출 범위 밖, Voice Profile placeholder 무음 전체 탈락.
- **실행**: PROXY_URL 기본값 오설정(5682), proxy 실패 무음 skip, specialist 점화 채널 부재(①②④용 ESCALATE 없음, risk 태그 미기재), verify-review-done이 리뷰 수행 여부 미검증.
- **반영**: proxy timeout 후 도착한 피드백 미회수(실증: 16건 중 14건 미반영), fix 산출 텍스트 재검수 게이트 부재(실증: fix가 비문 4건 생성), 리뷰어 완성 대체문의 문체 이식.

## Changes

### A. compile_brief.py (v2.1.0)

- `COMPILE_BRIEF_VERSION` 상수 + 브리프 헤더 스탬프
- knowledge-map **캐릭터별 표 형식 지원** (기존 매트릭스 형식과 병행) + 전역 지식 소유자 보존
- CLAUDE.md §8 추출 확장: §8.1 blockquote 기본값 + §8.2 상황 전환 + §8.3 어투 이력 (헤딩 접미사 허용)
- character-tracker 화이트리스트에 "대화 모드" 추가
- relationship 매트릭스 regex blockquote 허용
- Voice Profile subsection 단위 부분 포함 + `⚠️ 미추출` 경고
- episode-log header-aware 컬럼 매핑 (핵심 사건/엔딩 훅/등장인물 열 복구)
- foreshadowing 헤딩 alias `## 복선 현황` 허용
- **PARSE-MISS 리포트**: 소스 존재 + 섹션 결손 시 브리프 상단 경고 + events 기록
- knowledge-map `[PIN]` 행 상시 포함 (장편 초반 기억 소멸 방지) + 만남 로그 첫 만남 행 보존
- live cue 직결 상태 bullet 5→7
- 계약 테스트 신설 (배포 템플릿 원본을 fixture로 사용)

### B. 존댓말(④) 축 복구

- unified-reviewer 항목 6에 **실행 절차 부여** (화자쌍 스캔 → 어미 판별 → 매트릭스 대조 → 불일치 표 출력) + 출력 형식에 존댓말 검증 표
- `ESCALATE_SPEECH` / `ESCALATE_NATURALNESS` 신설 + batch-supervisor §2.5 즉시 대응 경로
- 공통 면책 5종 #3에 **트리거 가시성 조건** 부착 (4파일 동기: unified-reviewer / korean-naturalness / repetition-checker / narrative-fixer) + CLAUDE.md §8.4 규칙 4 동일 조건
- 3b-post step 6에 신규 캐릭터 03-characters + §8.1~8.3 등재 의무 추가
- `scripts/speech-level-scan.py` 신설 (결정론적 보조 스캐너 — 판정은 리뷰어)
- validate-settings.py에 §8.1 실기재 WARN + INIT-PROMPT §8.1 게이트 명시

### C. ①② 방어선 보강

- editor_server.py: `PROXY_URL` 기본값 5683 수정, `parse_claude_md` 기본 플래그 Phase 2 정합(proxy만 ON), compile_brief 버전 로깅
- proxy 실패 대응: 무음 skip 금지 — action-log 기록 + 연속 2화 실패 시 사용자 보고 + `/naturalness` 자동 대체 + **지연 도착 피드백 회수 절차** (batch-supervisor §3b-post 3)
- fix 재검수: patch_class=rewrite 시 수정 구간 ±1문단 proxy/naturalness 재검증 포함 (§3b-post 5e) + DEFER 명시 기록 (5f)
- 리뷰어 수정안 원칙: 결합/번역투/문체는 방향 서술 기본 (완성문 이식 금지) + fixer 측 대응 규칙 + fix-spec에 대표 문단 앵커 필드
- D절 Style 채택 게이트 명문화 (검출과 문안 제안 분리 — 외부 소스를 켜도 평균체 수렴을 막는 구조)
- continuity C 총 건수 계측 (캡 유지 + 신호만 상향)
- writer 읽기 목록에 01-style-guide §0~§4·§6 추가 (예문 앵커 도달 보장)
- codex-writer-role Korean Prose에 GPT 빈발 결합 7종 (방향 서술) / claude-writer-role에 명사화 평론체 anti-pattern 3종 (실증 기반)
- 01-style-guide §2.5 연재 매체 호흡 앵커 + §3 대사 비트 예문 + 프로파일별 대사:지문 앵커
- gpt_naturalness 주기 샘플링 (매 5화 중 1화 + 고위험 화)

### D. ③ 맥락 축 보강

- 요약 검증 E절: S1/S3/S6 경량 서브셋 **매 화** 승격 (갱신 행만 대상)
- verify-review-done.py 실질화: review-log 헤더 / action-log updated·skipped 토큰 / Carry-Forward 섹션 검사
- Brief sanity preflight (§2.5): 직결 앵커 부재·PARSE-MISS = 브리프 결함 판정
- auto-compact 손실 대응 (§5a): compact 감지 시 Chunk Start 승격 + writer prompt 주기 재독 규칙 ({N} % 5)
- 아크 F단계에 PIN 승격 절차 (11번)
- 3c 플롯 생성 프롬프트에 risk 태깅 지시

### E. 문서 정합 (드리프트 수리)

- stale §0.x 참조 수정 (§0.5 평균체→§0.7, §0.4 허용 이탈→§0.5), §3.2.4→§3.2 item 7
- "13 Items"→14항목 통일 (A절 헤더 + standard 출력)
- 존재하지 않는 "번역투 4패턴/8패턴" 목록 → korean-naturalness §-1·§1~5 정본 참조로 교체
- 존재하지 않는 "§4 Show/Tell 표" 참조 → 판단 기준 서술로 재작성
- claude-fixer "넣는"→"넘는" 오타 수정
- checker cadence 정본 선언 (07-periodic Specialist Cadence = canon, §4.1 등재) + repetition/pov-era 문서의 "5화마다" 제거
- fixer 1회 상한 vs 재리뷰 2회 상한 관계를 §4.1 Canon에 표로 명시
- codex-writer/claude-writer Review Surface "잔여 정밀 탐지" 역할 분리 (Drafting #2와의 이중 배정 해소)

## Rollback

- 이 phase는 단일 커밋으로 적용됨. `git revert {commit}` 으로 전체 롤백 가능.
- compile_brief.py만 롤백하려면 mcp-novel-editor 쪽 동기화 커밋도 함께 롤백해야 한다 (배포 이원화 재발 주의).

## Validation

- pytest 전체 green (46+; `test_contract_templates.py` 18개 신설 — 배포 템플릿 원본을 fixture로 사용)
- 골든 brief: 버전 스탬프 1줄 제외 바이트 동일 (하위 호환 입증)
- no-title-027 6화 실측 스모크: 결손 섹션 7종(약속/지식맵/에피소드/복선/금지사항/§8.2·8.3/대화 모드) 전부 복구, PARSE-MISS 0건
- editor_server import + `parse_claude_md` 기본값 확인 (플래그 부재 시 proxy만 ON)
- `speech-level-scan.py` 실전 챕터(001-codex 2화) 스모크 — 대사 32건 분류·화자 힌트 정상
- `validate-settings.py` — 템플릿 자체의 §8.1/§0 placeholder를 정확히 WARN
- `validate-docs.py` — phase doc 구조 포함 FAIL 0 확인

## Dependencies

- Phase 2 (voice preservation) — 면책 5종·플래그 기본값 체계 위에 조건을 얹음
- Phase 6 (critical fixes) — promise header-aware 파싱 방식을 episode-log에 확장
- Phase 7 (WRITER-HOLD runtime) — fixer dissent 경로를 전제로 채택 게이트 설계

## Known Issues / Follow-ups

- 2단계 style-guide §A(Draft)/§B(Review) 물리 분리 (writer-template-review-notes.md 잔여 과제)
- lean 두 템플릿(claude/codex)으로의 포팅 — 이번 사이클은 hybrid만
- Phase 4.1: profile 필드의 compile_brief/writer/reviewer 자동 반영
- verify-review-done.py의 action-log 토큰 검사는 파일명 하드코딩 — Conditional 목록 변경 시 동기 필요

## References

- 감사 보고서: `/root/novel/hybrid-template-audit-2026-07-02.md` (4렌즈 원본 보고 부록 포함)
- 선행 분석: `/root/novel/writer-template-review-notes.md` (규칙 충돌 → 문장 경직, §0.8 적용)
- 실증 대상: `/root/novel/no-title-001-codex/`, `/root/novel/no-title-001-claude-only/`
