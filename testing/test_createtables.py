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


def test_droptables_without_force(conn):
    """droptables require the user to pass --force"""
    err = os.system("ethindex createtables")
    assert err == 0
    tables_before = find_tables(conn)
    err = os.system("ethindex droptables")
    assert err == 256  # exit code 1
    tables_after = find_tables(conn)
    assert tables_before == tables_after


def test_droptables_with_force(conn):
    err = os.system("ethindex createtables")
    assert err == 0
    err = os.system("ethindex droptables --force")
    assert err == 0

    tables = find_tables(conn)
    assert tables == []
