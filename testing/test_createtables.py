import os


def find_tables(conn):
    """return a list of tables"""
    with conn.cursor() as cur:
        cur.execute(
            "select table_name from information_schema.tables where table_schema='public'"
        )
        return cur.fetchall()


def test_createtables(conn):
    err = os.system("ethindex createtables")
    assert err == 0
    tables = find_tables(conn)
    print("FOUND", tables)
    assert len(tables) >= 3
