import os


def test_createtables(postgresql_dsn):
    print("DSN:", postgresql_dsn)
    err = os.system("ethindex createtables")
    assert err == 0
