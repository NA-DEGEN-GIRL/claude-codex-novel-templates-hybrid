크로스 에피소드 반복 패턴을 전수 검사한다.

## 사용법

`/repetition-check` 또는 `/repetition-check N-M`

- 인자 없음: 전체 에피소드 검사 (아크 경계 모드: 메타스캔→본문 정밀)
- 범위: 해당 화수만 검사 (정기 모드: 본문 직접)

## 절차

### 정기 모드 (범위 지정 시)

1. 지정 범위의 에피소드 본문을 모두 읽는다
2. `summaries/repetition-watchlist.md`와 `summaries/style-lexicon.md`를 읽는다
3. `.claude/agents/repetition-checker.md`의 4개 범주(R1-R4)로 분석
4. 5축 테스트로 의도/습관 판정
5. 결과를 `summaries/cross-episode-repetition-report.md`에 저장
6. watchlist 갱신

### 아크 경계 모드 (범위 미지정 시)

1. **1단계 메타 스캔**: `summaries/episode-log.md`에서 전체 아크의 오프닝/엔딩/장면유형 태그를 분석
2. 의심 구간 식별 (같은 태그 3회+ 연속, 같은 엔딩 유형 연속 등)
3. **2단계 본문 정밀**: 의심 구간의 에피소드 본문만 직접 읽고 상세 분석
4. 결과를 `summaries/cross-episode-repetition-report.md`에 저장
5. watchlist 갱신

## 출력

`summaries/cross-episode-repetition-report.md` + `summaries/repetition-watchlist.md` 갱신

## 후속 처리

HIGH 항목이 있으면 `/narrative-fix --source repetition`으로 수정한다.
