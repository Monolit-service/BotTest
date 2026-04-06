from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ChannelScope(StrEnum):
    CHANNEL_1 = "channel_1"
    CHANNEL_2 = "channel_2"
    BUNDLE = "bundle"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"


class PaymentMethod(StrEnum):
    STARS = "stars"
    CRYPTOBOT = "cryptobot"


class SubscriptionStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    payments: Mapped[list[Payment]] = relationship(back_populates="user")
    subscriptions: Mapped[list[Subscription]] = relationship(back_populates="user")


class Plan(Base):
    __tablename__ = "plans"
    __table_args__ = (UniqueConstraint("code", name="uq_plan_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(1000))
    channel_scope: Mapped[str] = mapped_column(String(50))
    duration_days: Mapped[int] = mapped_column(Integer)
    price_xtr: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(default=True)

    payments: Mapped[list[Payment]] = relationship(back_populates="plan")
    subscriptions: Mapped[list[Subscription]] = relationship(back_populates="plan")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id", ondelete="CASCADE"), index=True)
    payload: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    payment_method: Mapped[str] = mapped_column(String(50), default=PaymentMethod.STARS)
    telegram_payment_charge_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_payment_charge_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount_xtr: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50), default=PaymentStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped[User] = relationship(back_populates="payments")
    plan: Mapped[Plan] = relationship(back_populates="payments")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(50), default=SubscriptionStatus.ACTIVE)
    starts_at: Mapped[datetime] = mapped_column(DateTime)
    ends_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="subscriptions")
    plan: Mapped[Plan] = relationship(back_populates="subscriptions")
