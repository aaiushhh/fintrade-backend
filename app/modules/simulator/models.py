"""Simulator module — database models for trading simulator."""

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
    JSON,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class SimulatorProfile(Base):
    """Prop-firm style profile with configurable rules."""
    __tablename__ = "simulator_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    initial_balance = Column(Float, default=100000.0)
    daily_loss_limit = Column(Float, default=5000.0)
    max_position_size = Column(Float, default=50000.0)
    stop_loss_required = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<SimulatorProfile {self.name}>"


class SimulatorAccount(Base):
    """Virtual trading account for a student."""
    __tablename__ = "simulator_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    profile_id = Column(Integer, ForeignKey("simulator_profiles.id"), nullable=True)
    balance = Column(Float, default=100000.0)
    initial_balance = Column(Float, default=100000.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # relationships
    trades = relationship("Trade", back_populates="account", cascade="all, delete-orphan")
    positions = relationship("Position", back_populates="account", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="account", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SimulatorAccount user={self.user_id} balance={self.balance}>"


class Trade(Base):
    """Completed or active trade record."""
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("simulator_accounts.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # buy, sell
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    pnl = Column(Float, nullable=True)
    status = Column(String(20), default="open")  # open, closed
    opened_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    closed_at = Column(DateTime(timezone=True), nullable=True)

    # relationships
    account = relationship("SimulatorAccount", back_populates="trades")

    def __repr__(self):
        return f"<Trade {self.symbol} {self.side} qty={self.quantity}>"


class Position(Base):
    """Currently open position."""
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("simulator_accounts.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=True)
    unrealized_pnl = Column(Float, default=0.0)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    opened_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # relationships
    account = relationship("SimulatorAccount", back_populates="positions")

    def __repr__(self):
        return f"<Position {self.symbol} {self.side} qty={self.quantity}>"


class Order(Base):
    """Order record (market/limit)."""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("simulator_accounts.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)
    order_type = Column(String(20), default="market")  # market, limit
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=True)
    status = Column(String(20), default="filled")  # pending, filled, cancelled
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # relationships
    account = relationship("SimulatorAccount", back_populates="orders")

    def __repr__(self):
        return f"<Order {self.symbol} {self.side} {self.order_type}>"


class RiskRule(Base):
    """Configurable risk rules per profile."""
    __tablename__ = "risk_rules"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("simulator_profiles.id", ondelete="CASCADE"), nullable=False)
    rule_type = Column(String(50), nullable=False)  # daily_loss_limit, max_position_size, stop_loss_required
    value = Column(Float, nullable=False)
    description = Column(Text, nullable=True)

    def __repr__(self):
        return f"<RiskRule {self.rule_type}={self.value}>"


class PerformanceMetric(Base):
    """Computed performance analytics for an account."""
    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("simulator_accounts.id", ondelete="CASCADE"), nullable=False, unique=True)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    total_pnl = Column(Float, default=0.0)
    win_rate = Column(Float, default=0.0)
    avg_win = Column(Float, default=0.0)
    avg_loss = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    risk_score = Column(Float, default=50.0)  # 0-100, lower is better
    consistency_score = Column(Float, default=50.0)  # 0-100, higher is better
    computed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<PerformanceMetric account={self.account_id} pnl={self.total_pnl}>"
