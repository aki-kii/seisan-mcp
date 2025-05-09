from collections.abc import Sequence
from typing import TypeVar, cast

from sqlalchemy import CheckConstraint, Index, create_engine, select
from sqlalchemy.orm import Mapped, Session, declarative_base, mapped_column

Base = declarative_base()
engine = create_engine("sqlite:///database/seisan.db")


class HomeCharge(Base):
    __tablename__ = "home_charge"

    id: Mapped[int] = mapped_column(primary_key=True)
    location: Mapped[str] = mapped_column(nullable=False)
    amount: Mapped[int] = mapped_column(nullable=False)

    @classmethod
    def get_home_charge(cls) -> "HomeCharge":
        """在宅チャージのレコードを取得"""
        with Session(engine) as session:
            stmt = select(cls).where(cls.location == "在宅チャージ")
            result = session.scalars(stmt).first()

        return result


T = TypeVar("T", bound="Transportation")


class Transportation(Base):
    """交通費情報の基底クラス"""

    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True)
    location: Mapped[str] = mapped_column(unique=True, nullable=False)
    departure: Mapped[str] = mapped_column(nullable=False)
    destination: Mapped[str] = mapped_column(nullable=False)
    amount: Mapped[int] = mapped_column(nullable=False)
    is_default: Mapped[int] = mapped_column(nullable=False, default=0)

    @classmethod
    def get_default(cls: type[T]) -> T:
        """デフォルトの交通費情報を取得する"""
        with Session(engine) as session:
            stmt = select(cls).where(cls.is_default == 1)
            result = session.scalars(stmt).first()

        return cast(T, result)

    @classmethod
    def get_all(cls: type[T]) -> Sequence[T]:
        """すべての交通費情報を取得する"""
        with Session(engine) as session:
            stmt = select(cls)
            result = session.scalars(stmt).all()

        return cast(Sequence[T], result)


class CompanyTransportation(Transportation):
    __tablename__ = "company_transportation"

    is_default: Mapped[int] = mapped_column(nullable=False, default=0)

    __table_args__ = (
        CheckConstraint("is_default IN (0, 1)", name="check_is_default"),
        Index("idx_company_default", is_default, unique=True, sqlite_where=is_default == 1),
    )


class CustomerTransportation(Transportation):
    __tablename__ = "customer_transportation"

    is_default: Mapped[int] = mapped_column(nullable=False, default=0)

    __table_args__ = (
        CheckConstraint("is_default IN (0, 1)", name="check_is_default"),
        Index("idx_customer_default", is_default, unique=True, sqlite_where=is_default == 1),
    )
