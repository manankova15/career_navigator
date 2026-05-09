"""Session factory wiring."""

from unittest.mock import MagicMock, patch


def test_get_db_closes_session():
    from app.database import get_db

    sess = MagicMock()
    with patch("app.database.SessionLocal", return_value=sess):
        gen = get_db()
        next(gen)
        gen.close()
    sess.close.assert_called_once()
