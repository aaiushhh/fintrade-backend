"""Offers module — database models."""

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class Offer(Base):
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    discount_type = Column(String(50), default="percentage")  # percentage, fixed
    discount_value = Column(Float, nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="SET NULL"), nullable=True)
    created_by_admin = Column(Integer, ForeignKey("users.id"), nullable=True)
    distributor_id = Column(Integer, ForeignKey("distributors.id", ondelete="SET NULL"), nullable=True)
    max_redemptions = Column(Integer, default=0)  # 0 = unlimited
    current_redemptions = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    valid_from = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    valid_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # relationships
    redemptions = relationship("OfferRedemption", back_populates="offer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Offer {self.code}>"


class OfferRedemption(Base):
    __tablename__ = "offer_redemptions"

    id = Column(Integer, primary_key=True, index=True)
    offer_id = Column(Integer, ForeignKey("offers.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    redeemed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    original_price = Column(Float, default=0.0)
    discounted_price = Column(Float, default=0.0)

    # relationships
    offer = relationship("Offer", back_populates="redemptions")

    def __repr__(self):
        return f"<OfferRedemption user={self.user_id} offer={self.offer_id}>"
