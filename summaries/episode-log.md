# Episode Log

<!--
  === compile_brief 헤딩/포맷 계약 (파서가 이 형식을 기대한다) ===

  - 첫 표의 헤더 행에서 컬럼 인덱스를 이름으로 찾는다 (header-aware). 컬럼 순서를 바꿔도 되지만
    아래 컬럼명 키워드는 유지한다: `요약`, `장소`, `등장인물`, `핵심 사건`, `엔딩 훅`.
    (구형 2열 `| 화 | 제목 | 요약 |` 형식도 호환 — `제목` 열이 있으면 제목으로 인식.)
  - `화` 열(첫 열)은 숫자여야 한다. compile_brief는 집필 대상 화수 이전의 마지막 3화를 싣는다.
  - `등장인물` 열은 자동 등장인물 감지(플롯에서 못 찾을 때)의 우선 소스로 쓰인다.
    쉼표/·/、 등으로 구분해 이름을 나열한다.
-->

| 화 | 요약 | 장소 | 등장인물 | 핵심 사건 | 엔딩 훅 | 오프닝 유형 | 엔딩 유형 | 장면 유형 |
|----|------|------|----------|----------|---------|-----------|----------|----------|

<!-- 오프닝 유형: action / dialogue / description / aftermath / question / flashback
     엔딩 유형: cliffhanger / reveal / decision / emotion / calm / question
     장면 유형(핵심 1-2개): combat / training / relationship / mystery / politics / travel / daily / crisis / info-delivery

     이 태그는 repetition-checker의 아크 경계 메타스캔에서 사용된다.
     writer가 summary update(step 8) 시 매 화 기록한다. -->
