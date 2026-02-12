# 한국은행 통화정책 온톨로지 — TypeDB 질의 시나리오 (검증본)

## 문법 안내

본 문서의 쿼리는 **TypeDB 3.x TypeQL** 문법을 기준으로 작성되었습니다.

**핵심 문법 규칙:**
- **match에서 relation 매칭**: `$rel isa relation-type, links (role: $player, ...);`
- **fetch JSON 프로젝션**: `fetch { "key": $var.attr-type };`
- **파이프라인 순서**: `match → sort → select → offset → limit → fetch`
- **속성 접근**: match에서는 `has attr $var`, fetch에서는 `$var.attr-type`

> ⚠️ 스키마(`bok-schema`)는 TypeDB 2.x `define` 문법으로 작성되어 있습니다.
> TypeDB 3.x에서는 일부 스키마 구문이 변경되었으므로(예: `sub` → `sub`,  `@abstract` 어노테이션 등),
> 실제 배포 시 스키마를 3.x에 맞게 조정하거나, 2.x 호환 모드에서 실행해야 합니다.
> 아래 쿼리는 **데이터가 이미 적재된 상태**에서 read 트랜잭션으로 실행하는 것을 전제합니다.

---

## 시나리오 1: 기준금리 결정 이력 조회

### 자연어 질의
> "2024년 이후 모든 기준금리 결정을 시간순으로 보여주세요."

### TypeQL (get — 테이블 형태 반환)

```tql
match
$pd isa policy-decision,
  links (source-doc: $doc, decision-maker: $m, target-indicator: $ind),
  has decision-date $date,
  has decision-type $type,
  has decision-value $val,
  has rationale $rat;
$ind has indicator-name "기준금리";
$m has member-name $name;
$doc has doc-id $did;
sort $date asc;
```

### TypeQL (fetch — JSON 형태 반환)

```tql
match
$pd isa policy-decision,
  links (source-doc: $doc, decision-maker: $m, target-indicator: $ind),
  has decision-date $date,
  has decision-type $type,
  has decision-value $val,
  has rationale $rat;
$ind has indicator-name "기준금리";
$m has member-name $name;
$doc has doc-id $did;
sort $date asc;
fetch {
  "의사록": $doc.doc-id,
  "결정일": $date,
  "유형": $type,
  "금리": $val,
  "의장": $name,
  "근거": $rat
};
```

### 기대 결과 (5건)

| 결정일 | 유형 | 금리(%) | 의사록 |
|--------|------|---------|--------|
| 2024-01-25 | 동결 | 3.50 | MPM-2024-01 |
| 2024-04-12 | 동결 | 3.50 | MPM-2024-04 |
| 2024-07-11 | 동결 | 3.50 | MPM-2024-07 |
| 2024-10-11 | 인하 | 3.25 | MPM-2024-10 |
| 2025-01-16 | 인하 | 3.00 | MPM-2025-01 |

---

## 시나리오 2: 정책 기조 전환점 탐지 (decision-chain)

### 자연어 질의
> "동결에서 인하로 기조가 전환된 시점과 그 근거는?"

### TypeQL

```tql
match
$chain isa decision-chain,
  links (prior-decision: $d1, subsequent-decision: $d2),
  has chain-rationale $reason,
  has time-gap-days $gap;
$d1 has decision-type "동결",
  has decision-date $date1,
  has decision-value $val1;
$d2 has decision-type "인하",
  has decision-date $date2,
  has decision-value $val2;
fetch {
  "이전결정일": $date1,
  "이전금리": $val1,
  "전환결정일": $date2,
  "전환금리": $val2,
  "간격일수": $gap,
  "전환근거": $reason
};
```

### 기대 결과 (1건)

동결(2024-07-11, 3.50%) → 인하(2024-10-11, 3.25%), 92일 간격.
"물가 목표 수렴 확인 및 경기 하방 리스크 확대로 동결에서 인하로 기조 전환."

---

## 시나리오 3: 소수의견 전체 조회 (dissent)

### 자연어 질의
> "소수의견을 낸 위원, 대상 결정, 의견 내용을 보여주세요."

### TypeQL

```tql
match
$dis isa dissent,
  links (dissenter: $m, target-decision: $d),
  has dissent-opinion $opinion,
  has dissent-rationale $reason;
$m has member-name $name,
  has role-name $role;
$d has decision-date $date,
  has decision-type $majority,
  has decision-value $val;
sort $date asc;
fetch {
  "위원": $name,
  "직책": $role,
  "회의일": $date,
  "다수결정": $majority,
  "금리": $val,
  "소수의견": $opinion,
  "근거": $reason
};
```

### 기대 결과 (4건)

| 위원 | 회의일 | 다수결정 | 소수의견 |
|------|--------|---------|---------|
| 박기영 | 2024-07-11 | 동결(3.50%) | 25bp 인하 |
| 서영경 | 2024-10-11 | 인하(3.25%) | 동결 |
| 서영경 | 2025-01-16 | 인하(3.00%) | 동결 |
| 정규일 | 2025-01-16 | 인하(3.00%) | 50bp 인하 |

---

## 시나리오 4: 특정 위원의 소수의견 이력

### 자연어 질의
> "서영경 위원이 반대한 결정들을 보여주세요."

### TypeQL

```tql
match
$dis isa dissent,
  links (dissenter: $m, target-decision: $d),
  has dissent-opinion $opinion,
  has dissent-rationale $reason;
$m has member-name "서영경";
$d has decision-date $date,
  has decision-type $majority,
  has decision-value $val;
sort $date asc;
fetch {
  "회의일": $date,
  "다수결정": $majority,
  "금리": $val,
  "서영경의견": $opinion,
  "근거": $reason
};
```

### 기대 결과 (2건)
일관된 매파(hawkish) 성향 — 두 번 모두 인하 결정에 대해 "동결"을 주장.

---

## 시나리오 5: GDP 전망 수정 이력 추적 (forecast-revision)

### 자연어 질의
> "GDP 성장률 전망이 어떻게 바뀌었나요? 수정 사유 포함."

### TypeQL

```tql
match
$rev isa forecast-revision,
  links (original-forecast: $f1, revised-forecast: $f2),
  has revision-direction $dir,
  has revision-magnitude $mag,
  has revision-reason $reason;
$f1 isa forecast,
  links (target-indicator: $ind),
  has forecast-value $v1,
  has forecast-date $date1,
  has forecast-period $period1;
$f2 has forecast-value $v2,
  has forecast-date $date2,
  has forecast-period $period2;
$ind has indicator-name "GDP성장률";
sort $date1 asc;
fetch {
  "원래전망일": $date1,
  "원래값": $v1,
  "수정전망일": $date2,
  "수정값": $v2,
  "방향": $dir,
  "폭": $mag,
  "사유": $reason
};
```

### 기대 결과 (2건)

| 원래값 | 수정값 | 방향 | 폭 | 사유 |
|--------|--------|------|-----|------|
| 2.1% | 2.4% | 상향 | 0.3 | 반도체 수출 호조 |
| 2.4% | 1.8% | 하향 | 0.6 | 글로벌 무역 둔화, 미중 관세 |

---

## 시나리오 6: 정책결정이 전망에 미친 영향 (forecast-impact)

### 자연어 질의
> "2024년 10월 금리 인하가 이후 경제전망에 어떤 영향을 미쳤나요?"

### TypeQL

```tql
match
$fi isa forecast-impact,
  links (triggering-decision: $d, affected-forecast: $f),
  has impact-description $desc,
  has impact-lag-months $lag;
$d has decision-date $ddate,
  has decision-type $dtype,
  has decision-value $dval;
$f isa forecast,
  links (target-indicator: $ind),
  has forecast-value $fval,
  has forecast-date $fdate,
  has forecast-period $fperiod;
$ind has indicator-name $iname;
fetch {
  "정책결정일": $ddate,
  "결정유형": $dtype,
  "금리": $dval,
  "전망일": $fdate,
  "대상기간": $fperiod,
  "지표": $iname,
  "전망값": $fval,
  "시차_개월": $lag,
  "영향설명": $desc
};
```

### 기대 결과 (1건)

인하(2024-10-11, 3.25%) → GDP전망(2025-02-18, 1.8%) — 4개월 시차.
"대외 불확실성이 통화정책 효과를 상쇄했음을 시사."

### 하이퍼릴레이션 핵심 가치
이 쿼리는 **relation(policy-decision)과 relation(forecast) 사이의 relation(forecast-impact)**을 질의합니다.
RDF에서는 양쪽 relation을 각각 reify한 뒤 연결해야 하므로 보조 노드가 최소 3개 필요합니다.

---

## 시나리오 7: 리스크 심각도 변화 추적 (risk-reassessment)

### 자연어 질의
> "2024년 동안 리스크 등급이 상향된 항목과 원인은?"

### TypeQL

```tql
match
$rr isa risk-reassessment,
  links (prior-assessment: $a1, updated-assessment: $a2),
  has severity-change "상향",
  has reassessment-reason $reason;
$a1 isa risk-assessment,
  links (risk-subject: $rf),
  has assessment-date $date1,
  has severity $sev1;
$a2 has assessment-date $date2,
  has severity $sev2;
$rf has risk-name $rname;
fetch {
  "리스크": $rname,
  "이전평가일": $date1,
  "이전등급": $sev1,
  "현재평가일": $date2,
  "현재등급": $sev2,
  "상향사유": $reason
};
```

### 기대 결과 (2건)

| 리스크 | 이전등급 | 현재등급 | 사유 |
|--------|---------|---------|------|
| 가계부채 | 보통 | 높음 | 기준금리 인하 이후 가계대출 재확대 |
| 부동산시장과열 | 낮음 | 높음 | 금리 인하 기대감으로 서울 주택가격 반등 |

---

## 시나리오 8: 리스크 전이 경로 분석

### 자연어 질의
> "가계부채에서 시작하는 리스크 전이 경로를 보여주세요."

### TypeQL — 직접 전이 (1-hop)

```tql
match
$rt isa risk-transmission,
  links (from-risk: $r1, to-risk: $r2),
  has transmission-mechanism $mech,
  has observed-date $date;
$r1 has risk-name "가계부채";
$r2 has risk-name $target;
fetch {
  "전이대상": $target,
  "메커니즘": $mech,
  "관찰일": $date
};
```

### TypeQL — 2단 전이 (2-hop)

```tql
match
$rt1 isa risk-transmission,
  links (from-risk: $r1, to-risk: $r2),
  has transmission-mechanism $mech1;
$rt2 isa risk-transmission,
  links (from-risk: $r2, to-risk: $r3),
  has transmission-mechanism $mech2;
$r1 has risk-name "가계부채";
$r2 has risk-name $mid;
$r3 has risk-name $end;
fetch {
  "중간리스크": $mid,
  "1차메커니즘": $mech1,
  "최종리스크": $end,
  "2차메커니즘": $mech2
};
```

### 기대 결과

```
가계부채
  ──[가계대출확대→주택구매자금유입→부동산가격상승]──▶
    부동산시장과열
      ──[부동산PF부실→건설사유동성위기→비은행연쇄부실]──▶
        기업신용리스크
```

---

## 시나리오 9: 문서 간 교차참조 네트워크 (cross-reference)

### 자연어 질의
> "2024년 10월 인하 결정을 참조한 모든 문서와 맥락은?"

### TypeQL

```tql
match
$cr isa cross-reference,
  links (referring-doc: $doc1, referred-doc: $doc2, referenced-decision: $d),
  has reference-context $ctx;
$d has decision-date 2024-10-11,
  has decision-type "인하";
$doc1 has doc-id $from_id,
  has title $from_title;
$doc2 has doc-id $to_id;
fetch {
  "참조문서": $from_id,
  "문서제목": $from_title,
  "참조대상": $to_id,
  "맥락": $ctx
};
```

### 기대 결과 (2건)

| 참조문서 | 참조대상 | 맥락 |
|---------|---------|------|
| FSR-2024-12 | MPM-2024-10 | 10월 인하 이후 가계대출 증가세 분석 |
| MPM-2024-10 | EOR-2024-H2 | 8월 전망보고서 수출 전망에도 내수 부진이 깊어 인하 근거로 활용 |

### 하이퍼릴레이션 핵심 가치
cross-reference는 **3개 role**(referring-doc, referred-doc, referenced-decision)을 가진 **3항 관계**입니다.
특히 `referenced-decision`은 **relation 타입(policy-decision)**이 role-player로 참여합니다.

---

## 시나리오 10: 전체 결정 체인 순회

### 자연어 질의
> "금리 결정의 연쇄(chain)를 처음부터 끝까지 보여주세요."

### TypeQL

```tql
match
$chain isa decision-chain,
  links (prior-decision: $d1, subsequent-decision: $d2),
  has chain-rationale $reason,
  has time-gap-days $gap;
$d1 has decision-date $date1,
  has decision-type $type1,
  has decision-value $val1;
$d2 has decision-date $date2,
  has decision-type $type2,
  has decision-value $val2;
sort $date1 asc;
fetch {
  "이전결정일": $date1,
  "이전유형": $type1,
  "이전금리": $val1,
  "다음결정일": $date2,
  "다음유형": $type2,
  "다음금리": $val2,
  "간격일수": $gap,
  "연결근거": $reason
};
```

### 기대 결과 (4건)

```
동결 3.50(01/25) ──78일──▶ 동결 3.50(04/12) ──90일──▶ 동결 3.50(07/11) ──92일──▶ 인하 3.25(10/11) ──97일──▶ 인하 3.00(01/16)
```

---

## 시나리오 11: 금융안정보고서 리스크 대시보드

### 자연어 질의
> "가장 최근 금융안정보고서의 리스크 평가 전체를 보여주세요."

### TypeQL

```tql
match
$ra isa risk-assessment,
  links (source-doc: $doc, risk-subject: $rf, related-indicator: $ind),
  has assessment-date $date,
  has severity $sev,
  has assessment-text $text;
$doc has doc-id "FSR-2024-12";
$rf has risk-name $rname,
  has risk-category $rcat;
$ind has indicator-name $iname;
fetch {
  "리스크": $rname,
  "분류": $rcat,
  "심각도": $sev,
  "관련지표": $iname,
  "평가": $text
};
```

### 기대 결과 (3건)

| 리스크 | 분류 | 심각도 | 관련지표 |
|--------|------|--------|---------|
| 가계부채 | 가계 | 높음 | 가계신용증가율 |
| 부동산시장과열 | 자산시장 | 높음 | 가계신용증가율 |
| 기업신용리스크 | 기업 | 보통 | 경상수지 |

---

## 시나리오 12: 전망보고서별 전망치 비교

### 자연어 질의
> "각 경제전망보고서의 GDP와 물가 전망치를 비교해주세요."

### TypeQL

```tql
match
$f isa forecast,
  links (source-doc: $doc, target-indicator: $ind),
  has forecast-date $date,
  has forecast-period $period,
  has forecast-value $val,
  has confidence-level $conf;
$doc has doc-id $did,
  has title $title;
$ind has indicator-name $iname;
sort $date asc;
fetch {
  "보고서": $did,
  "발표일": $date,
  "지표": $iname,
  "대상기간": $period,
  "전망값": $val,
  "신뢰도": $conf
};
```

### 기대 결과 (6건)

| 보고서 | 지표 | 대상기간 | 전망값 | 신뢰도 |
|--------|------|---------|--------|--------|
| EOR-2024-H1 | GDP성장률 | 2024 | 2.1 | 보통 |
| EOR-2024-H1 | 소비자물가상승률 | 2024 | 2.6 | 보통 |
| EOR-2024-H2 | GDP성장률 | 2024 | 2.4 | 높음 |
| EOR-2024-H2 | 소비자물가상승률 | 2024 | 2.3 | 높음 |
| EOR-2025-H1 | GDP성장률 | 2025 | 1.8 | 낮음 |
| EOR-2025-H1 | 소비자물가상승률 | 2025 | 2.0 | 높음 |

---

## 시나리오 13: 물가 전망 수정 내역

### 자연어 질의
> "소비자물가 전망이 어떻게 수정되었나요?"

### TypeQL

```tql
match
$rev isa forecast-revision,
  links (original-forecast: $f1, revised-forecast: $f2),
  has revision-direction $dir,
  has revision-magnitude $mag,
  has revision-reason $reason;
$f1 isa forecast,
  links (target-indicator: $ind),
  has forecast-value $v1,
  has forecast-date $d1;
$f2 has forecast-value $v2,
  has forecast-date $d2;
$ind has indicator-name "소비자물가상승률";
fetch {
  "원래전망일": $d1,
  "원래값": $v1,
  "수정전망일": $d2,
  "수정값": $v2,
  "방향": $dir,
  "폭": $mag,
  "사유": $reason
};
```

### 기대 결과 (1건)

2.6% → 2.3% (하향, 0.3%p) — "국제유가 안정 및 농산물 가격 하락"

---

## 시나리오 14: 특정 리스크의 전체 컨텍스트 조회

### 자연어 질의
> "가계부채 리스크의 평가 이력, 전이 경로, 등급 변화를 모두 보여주세요."

### TypeQL — Part A: 평가 이력

```tql
match
$ra isa risk-assessment,
  links (source-doc: $doc, risk-subject: $rf, related-indicator: $ind),
  has assessment-date $date,
  has severity $sev,
  has assessment-text $text;
$rf has risk-name "가계부채";
$doc has doc-id $did;
$ind has indicator-name $iname;
sort $date asc;
fetch {
  "보고서": $did,
  "평가일": $date,
  "심각도": $sev,
  "관련지표": $iname,
  "평가내용": $text
};
```

### TypeQL — Part B: 전이 경로

```tql
match
$rt isa risk-transmission,
  links (from-risk: $r1, to-risk: $r2),
  has transmission-mechanism $mech,
  has observed-date $date;
$r1 has risk-name "가계부채";
$r2 has risk-name $target;
fetch {
  "전이대상": $target,
  "메커니즘": $mech,
  "관찰일": $date
};
```

### TypeQL — Part C: 등급 변화

```tql
match
$rr isa risk-reassessment,
  links (prior-assessment: $a1, updated-assessment: $a2),
  has severity-change $change,
  has reassessment-reason $reason;
$a1 isa risk-assessment,
  links (risk-subject: $rf),
  has severity $sev1,
  has assessment-date $date1;
$a2 has severity $sev2,
  has assessment-date $date2;
$rf has risk-name "가계부채";
fetch {
  "이전평가일": $date1,
  "이전등급": $sev1,
  "현재평가일": $date2,
  "현재등급": $sev2,
  "변화방향": $change,
  "사유": $reason
};
```

---

## 시나리오 15: 10월 인하 결정 360도 종합 분석

### 자연어 질의
> "2024년 10월 인하의 전체 파급을 보여주세요 — 소수의견, 후속 결정, 전망 영향, 문서 참조 모두."

### TypeQL — Part A: 소수의견

```tql
match
$dis isa dissent,
  links (dissenter: $m, target-decision: $d),
  has dissent-opinion $opinion,
  has dissent-rationale $reason;
$d has decision-date 2024-10-11,
  has decision-type "인하";
$m has member-name $name;
fetch {
  "위원": $name,
  "소수의견": $opinion,
  "근거": $reason
};
```

### TypeQL — Part B: 후속 결정 체인

```tql
match
$chain isa decision-chain,
  links (prior-decision: $d1, subsequent-decision: $d2),
  has chain-rationale $reason,
  has time-gap-days $gap;
$d1 has decision-date 2024-10-11,
  has decision-type "인하";
$d2 has decision-date $next_date,
  has decision-type $next_type,
  has decision-value $next_val;
fetch {
  "후속결정일": $next_date,
  "후속유형": $next_type,
  "후속금리": $next_val,
  "간격일수": $gap,
  "연결근거": $reason
};
```

### TypeQL — Part C: 전망 영향

```tql
match
$fi isa forecast-impact,
  links (triggering-decision: $d, affected-forecast: $f),
  has impact-description $desc,
  has impact-lag-months $lag;
$d has decision-date 2024-10-11,
  has decision-type "인하";
$f isa forecast,
  links (target-indicator: $ind),
  has forecast-value $fval,
  has forecast-period $period;
$ind has indicator-name $iname;
fetch {
  "지표": $iname,
  "대상기간": $period,
  "전망값": $fval,
  "시차_개월": $lag,
  "영향설명": $desc
};
```

### TypeQL — Part D: 문서 교차참조

```tql
match
$cr isa cross-reference,
  links (referring-doc: $doc1, referred-doc: $doc2, referenced-decision: $d),
  has reference-context $ctx;
$d has decision-date 2024-10-11,
  has decision-type "인하";
$doc1 has doc-id $from_id,
  has title $from_title;
fetch {
  "참조문서": $from_id,
  "문서제목": $from_title,
  "맥락": $ctx
};
```

### 종합 다이어그램

> "2024년 10월 인하의 전체 파급을 보여주세요 — 소수의견, 후속 결정, 전망 영향, 문서 참조 모두."

```
                        ┌─ 소수의견 ───────────────────┐
                        │  서영경: "동결" (가계부채 우려)  │
                        └────────────────────────────┘
                                     │
   ┌── 선행 결정 ──┐          ┌────────┴────────┐          ┌─ 후속 결정 ──────┐
   │ 2024-07-11  │──chain──▶│  2024-10-11     │──chain──▶│ 2025-01-16     │
   │ 동결 3.50%   │  92일     │  인하 3.25%      │  97일    │ 인하 3.00%      │
   └─────────────┘          └────────┬────────┘          └────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
              ┌─ 전망 영향 ─┐   ┌── 교차참조 ──┐   ┌─ 리스크 파급 ──────┐
              │ 2025 GDP  │   │ FSR-2024-12│   │ 가계부채: 보통→높음 │
              │ 1.8% 하향  │   │ MPM-2025-01│   │ 부동산: 낮음→높음   │
              │ 시차: 4개월 │   └────────────┘   └─────────────────┘
              └───────────┘
```

---

## 부록 A: TypeDB 3.x vs 2.x 주요 문법 차이

| 항목 | TypeDB 2.x | TypeDB 3.x |
|------|-----------|-----------|
| relation 매칭 | `(role: $x) isa rel-type` | `$r isa rel-type, links (role: $x)` |
| fetch 절 | `fetch $x: attr-type;` | `fetch { "key": $x.attr-type };` |
| 변수 접두사 | `$` (인스턴스), `?` (값) | `$` (통합) |
| sort 위치 | fetch 내부 또는 get 뒤 | 파이프라인 스테이지 (match 뒤) |
| 옵셔널 매칭 | `not { ... }` 만 | `try { ... }` 추가 |
| 함수 | 없음 | `fun` 키워드로 재귀 함수 정의 가능 |

> **주의**: 위 스키마의 `define` 문법(특히 `@abstract`, `sub`, `plays`, `owns`)은 2.x 스타일입니다.
> TypeDB 3.x에서는 `@abstract` 어노테이션, `sub` 키워드 등은 호환되지만, 일부 세부 문법이 다를 수 있습니다.
> insert 데이터 파일의 `(role: $x) isa type` 구문은 3.x에서도 **insert 절에서는** 유효합니다.
> **match 절에서 relation을 찾을 때**는 반드시 `$r isa type, links (role: $x)` 패턴을 사용해야 합니다.

## 부록 B: 하이퍼릴레이션의 기술적 가치

| 질의 패턴 | TypeDB (하이퍼릴레이션) | RDF (reification 필요) |
|----------|----------------------|----------------------|
| decision-chain (결정→결정) | `$c isa decision-chain, links (prior: $d1, subseq: $d2)` | blank node + 4개 트리플 |
| dissent (위원×결정) | `$dis isa dissent, links (dissenter: $m, target: $d)` | rdf:Statement reification |
| forecast-impact (결정→전망) | `$fi isa forecast-impact, links (trigger: $d, affected: $f)` | 2단 reification |
| cross-reference (문서×문서×결정) | 3항 relation 직접 | blank node + 5개+ 트리플 |

**핵심:** TypeDB에서 relation은 다른 relation의 role에 직접 참여할 수 있어, "relation에 대한 relation"을 자연스럽게 표현합니다.

## 부록 C: 실행 가이드

```bash
# 1. 스키마 정의
typedb console --command="transaction <db> schema write" < bok-schema.tql

# 2. 데이터 적재 (PART 1 → 2 → 3 순서대로)
typedb console --command="transaction <db> data write" < bok_insert_data_v2_1.tql

# 3. 쿼리 실행 (read transaction)
typedb console --command="transaction <db> data read"
# 위 시나리오의 TypeQL을 붙여넣기하여 실행
```
