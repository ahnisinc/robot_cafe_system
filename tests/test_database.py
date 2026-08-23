from backend.database.db import (
    init_database
)


def test_database_initialization():

    init_database()

    assert True
