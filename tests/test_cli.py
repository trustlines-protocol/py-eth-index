import subprocess


def find_tables(conn):
    """return a list of tables"""
    with conn.cursor() as cur:
        cur.execute(
            "select table_name from information_schema.tables where table_schema='public'"
        )
        return cur.fetchall()


def test_createtables(conn):
    err = subprocess.call(["ethindex", "createtables"])
    assert err == 0
    tables = find_tables(conn)
    print("FOUND", tables)
    assert len(tables) >= 3


def test_droptables_without_force(conn):
    """droptables require the user to pass --force"""
    err = subprocess.call(["ethindex", "createtables"])
    assert err == 0
    tables_before = find_tables(conn)
    err = subprocess.call(["ethindex", "droptables"])
    assert err == 1
    tables_after = find_tables(conn)
    assert tables_before == tables_after


def test_droptables_with_force(conn):
    err = subprocess.call(["ethindex", "createtables"])
    assert err == 0
    err = subprocess.call(["ethindex", "droptables", "--force"])
    assert err == 0

    tables = find_tables(conn)
    assert tables == []


def test_importabi(conn, testenv):
    err = subprocess.call(["ethindex", "createtables"])
    assert err == 0
    err = subprocess.call(
        ["ethindex", "importabi", "--addresses", testenv.addresses_json_path]
    )
    assert err == 0
    with conn.cursor() as cur:
        cur.execute("select * from abis")
        abis = cur.fetchall()
        assert len(abis) == len(testenv.contract_addresses)


def test_importabi_replaces_abi(conn, testenv):
    err = subprocess.call(["ethindex", "createtables"])
    assert err == 0
    # import default abi
    subprocess.call(
        ["ethindex", "importabi", "--addresses", testenv.addresses_json_path]
    )
    # import custom test abi
    err = subprocess.call(
        [
            "ethindex",
            "importabi",
            "--addresses",
            testenv.addresses_json_path,
            "--contracts",
            testenv.contracts_json_path,
        ]
    )
    assert err == 0
    with conn.cursor() as cur:
        cur.execute("select * from abis")
        abis = cur.fetchall()

    # Look if the test function `emitUnknownAbiEvent` is now in the imported abi
    found = False
    for abi in abis[0]["abi"]:
        if "name" in abi.keys():
            if abi["name"] == "emitUnknownAbiEvent":
                found = True
    assert found
