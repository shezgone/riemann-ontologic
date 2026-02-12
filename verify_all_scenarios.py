"""
Bok-hyper 전체 시나리오 검증 스크립트
- 15개 시나리오의 기대결과를 조회하여 검증합니다.
"""
from typedb.driver import TypeDB, TransactionType, Credentials, DriverOptions
import traceback

DB = "Bok-hyper"

def scenario_1(tx):
    """시나리오 1: 기준금리 결정 이력 조회 (기대: 5건)"""
    print("=" * 70)
    print("시나리오 1: 기준금리 결정 이력 조회")
    print("=" * 70)
    q = """
    match
        $pd isa policy-decision,
            links (source-doc: $doc, decision-maker: $m, target-indicator: $ind),
            has decision-date $date,
            has decision-type $type,
            has decision-value $val;
        $ind has indicator-name "기준금리";
        $m has member-name $name;
        $doc has doc-id $did;
        sort $date asc;
    """
    rows = list(tx.query(q).resolve())
    print(f"  건수: {len(rows)} (기대: 5)")
    for r in rows:
        date = r.get("date").as_attribute().get_value()
        dtype = r.get("type").as_attribute().get_value()
        val = r.get("val").as_attribute().get_value()
        did = r.get("did").as_attribute().get_value()
        name = r.get("name").as_attribute().get_value()
        print(f"  {date} | {dtype} | {val}% | {did} | {name}")
    return len(rows) == 5


def scenario_2(tx):
    """시나리오 2: 동결→인하 기조 전환점 (기대: 1건)"""
    print("\n" + "=" * 70)
    print("시나리오 2: 정책 기조 전환점 탐지 (동결→인하)")
    print("=" * 70)
    q = """
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
    """
    rows = list(tx.query(q).resolve())
    print(f"  건수: {len(rows)} (기대: 1)")
    for r in rows:
        d1 = r.get("date1").as_attribute().get_value()
        v1 = r.get("val1").as_attribute().get_value()
        d2 = r.get("date2").as_attribute().get_value()
        v2 = r.get("val2").as_attribute().get_value()
        gap = r.get("gap").as_attribute().get_value()
        reason = r.get("reason").as_attribute().get_value()
        print(f"  동결({d1}, {v1}%) → 인하({d2}, {v2}%), {gap}일")
        print(f"  근거: {reason}")
    return len(rows) == 1


def scenario_3(tx):
    """시나리오 3: 소수의견 전체 조회 (기대: 4건)"""
    print("\n" + "=" * 70)
    print("시나리오 3: 소수의견 전체 조회")
    print("=" * 70)
    q = """
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
    """
    rows = list(tx.query(q).resolve())
    print(f"  건수: {len(rows)} (기대: 4)")
    for r in rows:
        name = r.get("name").as_attribute().get_value()
        role = r.get("role").as_attribute().get_value()
        date = r.get("date").as_attribute().get_value()
        majority = r.get("majority").as_attribute().get_value()
        val = r.get("val").as_attribute().get_value()
        opinion = r.get("opinion").as_attribute().get_value()
        print(f"  {name}({role}) | {date} | 다수:{majority}({val}%) | 소수:{opinion}")
    return len(rows) == 4


def scenario_4(tx):
    """시나리오 4: 서영경 위원 소수의견 이력 (기대: 2건)"""
    print("\n" + "=" * 70)
    print("시나리오 4: 서영경 위원 소수의견 이력")
    print("=" * 70)
    q = """
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
    """
    rows = list(tx.query(q).resolve())
    print(f"  건수: {len(rows)} (기대: 2)")
    for r in rows:
        date = r.get("date").as_attribute().get_value()
        majority = r.get("majority").as_attribute().get_value()
        val = r.get("val").as_attribute().get_value()
        opinion = r.get("opinion").as_attribute().get_value()
        reason = r.get("reason").as_attribute().get_value()
        print(f"  {date} | 다수:{majority}({val}%) | 서영경:{opinion} | {reason}")
    return len(rows) == 2


def scenario_5(tx):
    """시나리오 5: GDP 전망 수정 이력 (기대: 2건)"""
    print("\n" + "=" * 70)
    print("시나리오 5: GDP 전망 수정 이력")
    print("=" * 70)
    q = """
    match
        $rev isa forecast-revision,
            links (original-forecast: $f1, revised-forecast: $f2),
            has revision-direction $dir,
            has revision-magnitude $mag,
            has revision-reason $reason;
        $f1 isa forecast,
            links (source-doc: $doc1),
            has forecast-value $v1;
        $doc1 has doc-id $did1;
        $f2 has forecast-value $v2;
        $f1 links (target-indicator: $ind);
        $ind has indicator-name "GDP성장률";
    """
    rows = list(tx.query(q).resolve())
    print(f"  건수: {len(rows)} (기대: 2)")
    for r in rows:
        v1 = r.get("v1").as_attribute().get_value()
        v2 = r.get("v2").as_attribute().get_value()
        d = r.get("dir").as_attribute().get_value()
        mag = r.get("mag").as_attribute().get_value()
        reason = r.get("reason").as_attribute().get_value()
        print(f"  {v1}% → {v2}% | {d} | {mag} | {reason}")
    return len(rows) == 2


def scenario_6(tx):
    """시나리오 6: 정책결정→전망 영향 (기대: 1건)"""
    print("\n" + "=" * 70)
    print("시나리오 6: 2024.10 인하가 전망에 미친 영향")
    print("=" * 70)
    q = """
    match
        $fi isa forecast-impact,
            links (triggering-decision: $d, affected-forecast: $f),
            has impact-description $desc,
            has impact-lag-months $lag;
        $d has decision-date $ddate,
            has decision-type $dtype,
            has decision-value $dval;
        $f isa forecast,
            links (source-doc: $fdoc),
            has forecast-value $fval;
        $fdoc has doc-id $fdid;
    """
    rows = list(tx.query(q).resolve())
    print(f"  건수: {len(rows)} (기대: 1)")
    for r in rows:
        ddate = r.get("ddate").as_attribute().get_value()
        dtype = r.get("dtype").as_attribute().get_value()
        dval = r.get("dval").as_attribute().get_value()
        fval = r.get("fval").as_attribute().get_value()
        lag = r.get("lag").as_attribute().get_value()
        desc = r.get("desc").as_attribute().get_value()
        fdid = r.get("fdid").as_attribute().get_value()
        print(f"  {dtype}({ddate}, {dval}%) → {fdid} GDP {fval}% | 시차: {lag}개월")
        print(f"  설명: {desc}")
    return len(rows) == 1


def scenario_7(tx):
    """시나리오 7: 리스크 등급 상향 (기대: 2건)"""
    print("\n" + "=" * 70)
    print("시나리오 7: 2024년 리스크 등급 상향 추적")
    print("=" * 70)
    q = """
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
    """
    rows = list(tx.query(q).resolve())
    print(f"  건수: {len(rows)} (기대: 2)")
    for r in rows:
        rname = r.get("rname").as_attribute().get_value()
        sev1 = r.get("sev1").as_attribute().get_value()
        sev2 = r.get("sev2").as_attribute().get_value()
        reason = r.get("reason").as_attribute().get_value()
        print(f"  {rname}: {sev1} → {sev2} | {reason}")
    return len(rows) == 2


def scenario_8(tx):
    """시나리오 8: 리스크 전이 경로 (기대: 1-hop 1건, 2-hop 1건)"""
    print("\n" + "=" * 70)
    print("시나리오 8: 가계부채 리스크 전이 경로")
    print("=" * 70)
    
    # 1-hop
    q1 = """
    match
        $rt isa risk-transmission,
            links (from-risk: $r1, to-risk: $r2),
            has transmission-mechanism $mech,
            has observed-date $date;
        $r1 has risk-name "가계부채";
        $r2 has risk-name $target;
    """
    rows1 = list(tx.query(q1).resolve())
    print(f"  1-hop 건수: {len(rows1)} (기대: 1)")
    for r in rows1:
        target = r.get("target").as_attribute().get_value()
        mech = r.get("mech").as_attribute().get_value()
        print(f"  가계부채 → {target} | {mech}")
    
    # 2-hop
    q2 = """
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
    """
    rows2 = list(tx.query(q2).resolve())
    print(f"  2-hop 건수: {len(rows2)} (기대: 1)")
    for r in rows2:
        mid = r.get("mid").as_attribute().get_value()
        mech1 = r.get("mech1").as_attribute().get_value()
        end = r.get("end").as_attribute().get_value()
        mech2 = r.get("mech2").as_attribute().get_value()
        print(f"  가계부채 →[{mech1}]→ {mid} →[{mech2}]→ {end}")
    
    return len(rows1) == 1 and len(rows2) == 1


def scenario_9(tx):
    """시나리오 9: 교차참조 네트워크 (기대: 2건)"""
    print("\n" + "=" * 70)
    print("시나리오 9: 2024.10 인하 결정 교차참조")
    print("=" * 70)
    q = """
    match
        $cr isa cross-reference,
            links (referring-doc: $doc1, referred-doc: $doc2, referenced-decision: $d),
            has reference-context $ctx;
        $d has decision-date 2024-10-11T00:00:00,
            has decision-type "인하";
        $doc1 has doc-id $from_id,
            has title $from_title;
        $doc2 has doc-id $to_id;
    """
    rows = list(tx.query(q).resolve())
    print(f"  건수: {len(rows)} (기대: 2)")
    for r in rows:
        from_id = r.get("from_id").as_attribute().get_value()
        to_id = r.get("to_id").as_attribute().get_value()
        ctx = r.get("ctx").as_attribute().get_value()
        print(f"  {from_id} → {to_id} | {ctx}")
    return len(rows) == 2


def scenario_10(tx):
    """시나리오 10: 전체 결정 체인 순회 (기대: 4건)"""
    print("\n" + "=" * 70)
    print("시나리오 10: 금리 결정 체인 순회")
    print("=" * 70)
    q = """
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
    """
    rows = list(tx.query(q).resolve())
    print(f"  건수: {len(rows)} (기대: 4)")
    for r in rows:
        d1 = r.get("date1").as_attribute().get_value()
        t1 = r.get("type1").as_attribute().get_value()
        v1 = r.get("val1").as_attribute().get_value()
        d2 = r.get("date2").as_attribute().get_value()
        t2 = r.get("type2").as_attribute().get_value()
        v2 = r.get("val2").as_attribute().get_value()
        gap = r.get("gap").as_attribute().get_value()
        print(f"  {t1} {v1}%({d1}) ──{gap}일──▶ {t2} {v2}%({d2})")
    return len(rows) == 4


def scenario_11(tx):
    """시나리오 11: FSR-2024-12 리스크 대시보드 (기대: 3건)"""
    print("\n" + "=" * 70)
    print("시나리오 11: FSR-2024-12 리스크 대시보드")
    print("=" * 70)
    q = """
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
    """
    rows = list(tx.query(q).resolve())
    print(f"  건수: {len(rows)} (기대: 3)")
    for r in rows:
        rname = r.get("rname").as_attribute().get_value()
        rcat = r.get("rcat").as_attribute().get_value()
        sev = r.get("sev").as_attribute().get_value()
        iname = r.get("iname").as_attribute().get_value()
        print(f"  {rname}({rcat}) | {sev} | {iname}")
    return len(rows) == 3


def scenario_12(tx):
    """시나리오 12: 전망보고서별 비교 (기대: 6건)"""
    print("\n" + "=" * 70)
    print("시나리오 12: 전망보고서별 GDP/물가 비교")
    print("=" * 70)
    q = """
    match
        $f isa forecast,
            links (source-doc: $doc),
            has forecast-date $date,
            has forecast-period $period,
            has forecast-value $val,
            has confidence-level $conf;
        $doc has doc-id $did;
        $f links (target-indicator: $ind);
        $ind has indicator-name $iname;
        sort $date asc;
    """
    rows = list(tx.query(q).resolve())
    print(f"  건수: {len(rows)} (기대: 6)")
    for r in rows:
        did = r.get("did").as_attribute().get_value()
        iname = r.get("iname").as_attribute().get_value()
        period = r.get("period").as_attribute().get_value()
        val = r.get("val").as_attribute().get_value()
        conf = r.get("conf").as_attribute().get_value()
        print(f"  {did} | {iname} | {period} | {val}% | {conf}")
    return len(rows) == 6


def scenario_13(tx):
    """시나리오 13: 물가 전망 수정 (기대: 1건)"""
    print("\n" + "=" * 70)
    print("시나리오 13: 소비자물가 전망 수정 내역")
    print("=" * 70)
    q = """
    match
        $rev isa forecast-revision,
            links (original-forecast: $f1, revised-forecast: $f2),
            has revision-direction $dir,
            has revision-magnitude $mag,
            has revision-reason $reason;
        $f1 isa forecast,
            links (source-doc: $doc1),
            has forecast-value $v1;
        $doc1 has doc-id $d1;
        $f2 has forecast-value $v2;
        $f1 links (target-indicator: $ind);
        $ind has indicator-name "소비자물가상승률";
    """
    rows = list(tx.query(q).resolve())
    print(f"  건수: {len(rows)} (기대: 1)")
    for r in rows:
        v1 = r.get("v1").as_attribute().get_value()
        v2 = r.get("v2").as_attribute().get_value()
        d = r.get("dir").as_attribute().get_value()
        mag = r.get("mag").as_attribute().get_value()
        reason = r.get("reason").as_attribute().get_value()
        print(f"  {v1}% → {v2}% | {d} | {mag} | {reason}")
    return len(rows) == 1


def scenario_14(tx):
    """시나리오 14: 가계부채 전체 컨텍스트 (A: 평가이력 2건, B: 전이경로 1건, C: 등급변화 1건)"""
    print("\n" + "=" * 70)
    print("시나리오 14: 가계부채 전체 컨텍스트")
    print("=" * 70)
    
    # Part A: 평가 이력
    qa = """
    match
        $ra isa risk-assessment,
            links (source-doc: $doc, risk-subject: $rf),
            has assessment-date $date,
            has severity $sev,
            has assessment-text $text;
        $rf has risk-name "가계부채";
        $doc has doc-id $did;
        sort $date asc;
    """
    rowsa = list(tx.query(qa).resolve())
    print(f"  Part A (평가이력): {len(rowsa)}건 (기대: 2)")
    for r in rowsa:
        did = r.get("did").as_attribute().get_value()
        sev = r.get("sev").as_attribute().get_value()
        text = r.get("text").as_attribute().get_value()
        print(f"    {did} | {sev} | {text[:40]}...")
    
    # Part B: 전이 경로
    qb = """
    match
        $rt isa risk-transmission,
            links (from-risk: $r1, to-risk: $r2),
            has transmission-mechanism $mech,
            has observed-date $date;
        $r1 has risk-name "가계부채";
        $r2 has risk-name $target;
    """
    rowsb = list(tx.query(qb).resolve())
    print(f"  Part B (전이경로): {len(rowsb)}건 (기대: 1)")
    for r in rowsb:
        target = r.get("target").as_attribute().get_value()
        mech = r.get("mech").as_attribute().get_value()
        print(f"    → {target} | {mech}")
    
    # Part C: 등급 변화
    qc = """
    match
        $rr isa risk-reassessment,
            links (prior-assessment: $a1, updated-assessment: $a2),
            has severity-change $change,
            has reassessment-reason $reason;
        $a1 isa risk-assessment,
            links (risk-subject: $rf),
            has severity $sev1;
        $a2 has severity $sev2;
        $rf has risk-name "가계부채";
    """
    rowsc = list(tx.query(qc).resolve())
    print(f"  Part C (등급변화): {len(rowsc)}건 (기대: 1)")
    for r in rowsc:
        sev1 = r.get("sev1").as_attribute().get_value()
        sev2 = r.get("sev2").as_attribute().get_value()
        change = r.get("change").as_attribute().get_value()
        reason = r.get("reason").as_attribute().get_value()
        print(f"    {sev1} → {sev2} | {change} | {reason}")
    
    return len(rowsa) == 2 and len(rowsb) == 1 and len(rowsc) == 1


def scenario_15(tx):
    """시나리오 15: 10월 인하 360도 종합 분석"""
    print("\n" + "=" * 70)
    print("시나리오 15: 2024.10 인하 360도 종합 분석")
    print("=" * 70)
    
    # Part A: 소수의견 (기대: 1건 - 서영경)
    qa = """
    match
        $dis isa dissent,
            links (dissenter: $m, target-decision: $d),
            has dissent-opinion $opinion,
            has dissent-rationale $reason;
        $d has decision-date 2024-10-11T00:00:00,
            has decision-type "인하";
        $m has member-name $name;
    """
    rowsa = list(tx.query(qa).resolve())
    print(f"  Part A (소수의견): {len(rowsa)}건 (기대: 1)")
    for r in rowsa:
        name = r.get("name").as_attribute().get_value()
        opinion = r.get("opinion").as_attribute().get_value()
        print(f"    {name}: {opinion}")
    
    # Part B: 후속 결정
    qb = """
    match
        $chain isa decision-chain,
            links (prior-decision: $d1, subsequent-decision: $d2),
            has chain-rationale $reason,
            has time-gap-days $gap;
        $d1 has decision-date 2024-10-11T00:00:00,
            has decision-type "인하";
        $d2 has decision-date $next_date,
            has decision-type $next_type,
            has decision-value $next_val;
    """
    rowsb = list(tx.query(qb).resolve())
    print(f"  Part B (후속결정): {len(rowsb)}건 (기대: 1)")
    for r in rowsb:
        nd = r.get("next_date").as_attribute().get_value()
        nt = r.get("next_type").as_attribute().get_value()
        nv = r.get("next_val").as_attribute().get_value()
        gap = r.get("gap").as_attribute().get_value()
        print(f"    → {nt} {nv}%({nd}), {gap}일")
    
    # Part C: 전망 영향
    qc = """
    match
        $fi isa forecast-impact,
            links (triggering-decision: $d, affected-forecast: $f),
            has impact-description $desc,
            has impact-lag-months $lag;
        $d has decision-date 2024-10-11T00:00:00,
            has decision-type "인하";
        $f isa forecast,
            links (source-doc: $fdoc),
            has forecast-value $fval;
        $fdoc has doc-id $fdid;
    """
    rowsc = list(tx.query(qc).resolve())
    print(f"  Part C (전망영향): {len(rowsc)}건 (기대: 1)")
    for r in rowsc:
        fval = r.get("fval").as_attribute().get_value()
        lag = r.get("lag").as_attribute().get_value()
        desc = r.get("desc").as_attribute().get_value()
        print(f"    GDP {fval}%, 시차 {lag}개월 | {desc[:50]}...")
    
    # Part D: 문서 교차참조
    qd = """
    match
        $cr isa cross-reference,
            links (referring-doc: $doc1, referred-doc: $doc2, referenced-decision: $d),
            has reference-context $ctx;
        $d has decision-date 2024-10-11T00:00:00,
            has decision-type "인하";
        $doc1 has doc-id $from_id;
    """
    rowsd = list(tx.query(qd).resolve())
    print(f"  Part D (교차참조): {len(rowsd)}건 (기대: 2)")
    for r in rowsd:
        from_id = r.get("from_id").as_attribute().get_value()
        ctx = r.get("ctx").as_attribute().get_value()
        print(f"    {from_id} | {ctx}")
    
    return len(rowsa) == 1 and len(rowsb) == 1 and len(rowsc) == 1 and len(rowsd) == 2


def main():
    print("=" * 70)
    print("  Bok-hyper 전체 15개 시나리오 검증")
    print("=" * 70 + "\n")
    
    driver = TypeDB.driver("http://localhost:1729", Credentials("admin", "password"), DriverOptions(False, None))
    
    try:
        with driver.transaction(DB, TransactionType.READ) as tx:
            results = {}
            results[1] = scenario_1(tx)
            results[2] = scenario_2(tx)
            results[3] = scenario_3(tx)
            results[4] = scenario_4(tx)
            results[5] = scenario_5(tx)
            results[6] = scenario_6(tx)
            results[7] = scenario_7(tx)
            results[8] = scenario_8(tx)
            results[9] = scenario_9(tx)
            results[10] = scenario_10(tx)
            results[11] = scenario_11(tx)
            results[12] = scenario_12(tx)
            results[13] = scenario_13(tx)
            results[14] = scenario_14(tx)
            results[15] = scenario_15(tx)
        
        print("\n\n" + "=" * 70)
        print("  최종 검증 결과 요약")
        print("=" * 70)
        all_pass = True
        for i in range(1, 16):
            status = "PASS" if results[i] else "FAIL"
            if not results[i]:
                all_pass = False
            print(f"  시나리오 {i:2d}: {status}")
        
        print()
        if all_pass:
            print("  >>> 전체 15개 시나리오 검증 통과!")
        else:
            print("  >>> 일부 시나리오 불일치 — 위 결과를 확인해주세요.")
    
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
    finally:
        driver.close()


if __name__ == "__main__":
    main()
