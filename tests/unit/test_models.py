from app.models import Base

def test_declarative_base_is_configured() -> None:
    assert Base.metadata is not None