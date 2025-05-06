from sqlalchemy import create_engine, select
from sqlalchemy.orm import Mapped, Session, declarative_base, mapped_column

# SQLAlchemyの設定
Base = declarative_base()
engine = create_engine("sqlite:///database/seisan.db")


# データベースモデル
class HomeCharge(Base):
    __tablename__ = "home_charge"

    id: Mapped[int] = mapped_column(primary_key=True)
    location: Mapped[str] = mapped_column()
    amount: Mapped[int] = mapped_column()


def get_session() -> Session:
    """データベースセッションを取得する"""
    return Session(engine)


def get_home_charge() -> HomeCharge:
    """在宅チャージのレコードを取得"""
    with get_session() as session:
        stmt = select(HomeCharge).where(HomeCharge.location == "在宅チャージ")
        home_charge = session.scalars(stmt).first()

    return home_charge
