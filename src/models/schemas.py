"""
SQLAlchemy models for portfolio backtesting database
"""
from sqlalchemy import Column, Integer, String, Date, DECIMAL, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Asset(Base):
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    asset_class = Column(String(50), nullable=False, index=True)
    expense_ratio = Column(DECIMAL(5, 4))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    daily_prices = relationship("DailyPrice", back_populates="asset", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Asset(symbol='{self.symbol}', name='{self.name}')>"

class DailyPrice(Base):
    __tablename__ = "daily_prices"
    
    date = Column(Date, primary_key=True)
    symbol = Column(String(10), ForeignKey("assets.symbol"), primary_key=True)
    open_price = Column(DECIMAL(12, 4))
    high_price = Column(DECIMAL(12, 4))
    low_price = Column(DECIMAL(12, 4))
    close_price = Column(DECIMAL(12, 4))
    adj_close = Column(DECIMAL(12, 4), nullable=False)
    volume = Column(BigInteger)
    dividend = Column(DECIMAL(8, 4), default=0)
    split_factor = Column(DECIMAL(8, 4), default=1)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    asset = relationship("Asset", back_populates="daily_prices")
    
    def __repr__(self):
        return f"<DailyPrice(symbol='{self.symbol}', date='{self.date}', adj_close={self.adj_close})>"

class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    allocation_hash = Column(String(64), unique=True, nullable=False, index=True)
    vti_weight = Column(DECIMAL(5, 4), nullable=False)
    vtiax_weight = Column(DECIMAL(5, 4), nullable=False)  
    bnd_weight = Column(DECIMAL(5, 4), nullable=False)
    total_return = Column(DECIMAL(8, 4))
    cagr = Column(DECIMAL(6, 4))
    volatility = Column(DECIMAL(6, 4))
    max_drawdown = Column(DECIMAL(6, 4))
    sharpe_ratio = Column(DECIMAL(6, 4))
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<PortfolioSnapshot(hash='{self.allocation_hash[:8]}...', cagr={self.cagr})>"
