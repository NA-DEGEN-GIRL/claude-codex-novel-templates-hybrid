소설의 서사 품질을 전체 리뷰한다. 연속성 오류가 아닌, "이야기가 아직 재밌는가"를 평가한다.

## 사용법

`/narrative-review` 또는 `/narrative-review arc-03`

- 인자 없음: 전체 소설 리뷰
- 아크 지정: 해당 아크만 리뷰 (전체 맥락은 참조)

## 실행

1. `.claude/agents/narrative-reviewer.md`를 읽고 지시에 따른다.
2. 본문을 **절대 수정하지 않는다**. 분석 + 보고서 작성만 수행한다.
3. 산출물: `summaries/narrative-review-report.md`
4. 수정은 `/narrative-fix`로 별도 실행한다.
