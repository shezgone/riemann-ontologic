"""
Bok-hyper DB 복구 스크립트
- DB 생성 → 스키마 적용 → 엔티티 → 릴레이션 → 하이퍼릴레이션 순서로 적재
"""
from typedb.driver import TypeDB, TransactionType, Credentials, DriverOptions
import re, sys, time

DB = "Bok-hyper"
ADDR = "http://localhost:1729"

def read_tql(path):
    with open(path, "r") as f:
        return f.read()

def parse_insert_blocks(tql_text):
    """TQL 파일에서 개별 insert/match-insert 블록을 분리"""
    lines = tql_text.split("\n")
    blocks = []
    current = []
    in_block = False
    
    for line in lines:
        stripped = line.strip()
        # 주석이나 빈 줄
        if stripped.startswith("#") or stripped.startswith("##") or stripped == "":
            if in_block and stripped == "":
                # 빈 줄은 블록 종료 신호일 수 있음
                # 하지만 블록 내부의 빈 줄일 수도 있으므로, 다음 줄 확인 필요
                current.append(line)
            continue
        
        if stripped.startswith("match") or stripped.startswith("insert"):
            if in_block and stripped.startswith("match"):
                # 이전 블록 저장
                block_text = "\n".join(current).strip()
                if block_text:
                    blocks.append(block_text)
                current = [line]
            elif in_block and stripped.startswith("insert") and not any(l.strip().startswith("match") for l in current):
                # 이전 독립 insert 블록 저장, 새 insert 시작
                block_text = "\n".join(current).strip()
                if block_text:
                    blocks.append(block_text)
                current = [line]
            else:
                if not in_block:
                    in_block = True
                current.append(line)
        else:
            if in_block:
                current.append(line)
    
    # 마지막 블록
    if current:
        block_text = "\n".join(current).strip()
        if block_text:
            blocks.append(block_text)
    
    return blocks

def parse_tql_statements(tql_text):
    """TQL 파일에서 개별 문(statement)을 분리
    
    블록 종류:
    1. insert ... ;  (독립 insert)
    2. match ... ; insert ... ;  (match-insert 쌍)
    
    새 'match' 또는 독립 'insert'가 나오면 이전 블록 종료
    """
    lines = tql_text.split("\n")
    statements = []
    current_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # 주석 줄 건너뛰기
        if stripped.startswith("#") or stripped.startswith("##"):
            continue
        
        # 빈 줄은 무시
        if stripped == "":
            continue
        
        # 새 블록 시작 감지: 'match' 또는 줄 시작이 'insert'
        if stripped.startswith("match") or stripped.startswith("insert"):
            # 이전 블록 저장 여부 확인
            if current_lines:
                # match 뒤에 insert가 오면 같은 블록
                has_match = any(l.strip().startswith("match") for l in current_lines)
                has_insert = any(l.strip().startswith("insert") for l in current_lines)
                
                if stripped.startswith("insert") and has_match and not has_insert:
                    # match 블록에 insert 추가 (같은 블록)
                    current_lines.append(line)
                    continue
                else:
                    # 이전 블록 저장 후 새 블록 시작
                    stmt = "\n".join(current_lines).strip()
                    if stmt:
                        statements.append(stmt)
                    current_lines = []
            
            current_lines.append(line)
        else:
            current_lines.append(line)
    
    # 남은 블록
    if current_lines:
        stmt = "\n".join(current_lines).strip()
        if stmt:
            statements.append(stmt)
    
    return statements


def main():
    print("=" * 60)
    print("  Bok-hyper DB 복구 시작")
    print("=" * 60)
    
    driver = TypeDB.driver(ADDR, Credentials("admin", "password"), DriverOptions(False, None))
    
    try:
        # Step 1: DB 생성 (이미 있으면 삭제 후 재생성)
        print("\n[1/5] 데이터베이스 생성...")
        dbs = driver.databases.all()
        db_names = [d.name for d in dbs]
        if DB in db_names:
            print(f"  기존 '{DB}' 삭제...")
            driver.databases.get(DB).delete()
        driver.databases.create(DB)
        print(f"  '{DB}' 생성 완료")
        
        # Step 2: 스키마 적용
        print("\n[2/5] 스키마 적용...")
        schema_tql = read_tql("src/schema/bok_schema.tql")
        # 주석 제거
        schema_lines = [l for l in schema_tql.split("\n") if not l.strip().startswith("##")]
        schema_clean = "\n".join(schema_lines)
        
        with driver.transaction(DB, TransactionType.SCHEMA) as tx:
            tx.query(schema_clean).resolve()
            tx.commit()
        print("  스키마 적용 완료")
        
        # Step 3: 엔티티 적재 (Part 1)
        print("\n[3/5] 엔티티 적재 (Part 1)...")
        part1_tql = read_tql("src/schema/bok_insert_part1_entities.tql")
        stmts1 = parse_tql_statements(part1_tql)
        print(f"  {len(stmts1)}개 insert 문 발견")
        for i, stmt in enumerate(stmts1):
            with driver.transaction(DB, TransactionType.WRITE) as tx:
                tx.query(stmt).resolve()
                tx.commit()
            print(f"  [{i+1}/{len(stmts1)}] 완료")
        print("  엔티티 적재 완료")
        
        # Step 4: 기본 릴레이션 적재 (Part 2)
        print("\n[4/5] 기본 릴레이션 적재 (Part 2)...")
        part2_tql = read_tql("src/schema/bok_insert_part2_relations.tql")
        stmts2 = parse_tql_statements(part2_tql)
        print(f"  {len(stmts2)}개 match-insert 문 발견")
        for i, stmt in enumerate(stmts2):
            with driver.transaction(DB, TransactionType.WRITE) as tx:
                tx.query(stmt).resolve()
                tx.commit()
            print(f"  [{i+1}/{len(stmts2)}] 완료")
        print("  기본 릴레이션 적재 완료")
        
        # Step 5: 하이퍼릴레이션 적재 (Part 3)
        print("\n[5/5] 하이퍼릴레이션 적재 (Part 3)...")
        part3_tql = read_tql("src/schema/bok_insert_part3_hyper_relations.tql")
        stmts3 = parse_tql_statements(part3_tql)
        print(f"  {len(stmts3)}개 match-insert 문 발견")
        for i, stmt in enumerate(stmts3):
            with driver.transaction(DB, TransactionType.WRITE) as tx:
                tx.query(stmt).resolve()
                tx.commit()
            print(f"  [{i+1}/{len(stmts3)}] 완료")
        print("  하이퍼릴레이션 적재 완료")
        
        print("\n" + "=" * 60)
        print("  Bok-hyper DB 복구 완료!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        driver.close()


if __name__ == "__main__":
    main()
