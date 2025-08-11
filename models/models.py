from decimal import Decimal
from sqlalchemy import Column, Integer, Float, String, Boolean, ForeignKey, DateTime, Text, Numeric, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, unique=True)
    username = Column(String)
    balance_usd = Column(Float, default=0.0)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    wallet_address = Column(String, nullable=True)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price_usd = Column(Numeric, nullable=False)
    city = Column(String, nullable=False)
    category = Column(String, nullable=False)
    district = Column(String, default="Центр")  # добавляем район
    created_at = Column(DateTime, default=datetime.utcnow)

    photos = relationship("ProductPhoto", back_populates="product", cascade="all, delete-orphan")


class ProductPhoto(Base):
    __tablename__ = "product_photos"

    id = Column(Integer, primary_key=True)
    file_id = Column(String)  # Telegram file_id
    product_id = Column(Integer, ForeignKey("products.id"))
    product = relationship("Product", back_populates="photos")


class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    photo_id = Column(String)  # Конкретная фотка, выданная пользователю
    price_usd = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class TopUpRequest(Base):
    __tablename__ = "topup_requests"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    amount_usd = Column(Float)
    expected_ltc = Column(Float)
    status = Column(String, default="waiting")  # waiting, confirmed, expired
    created_at = Column(DateTime, default=datetime.utcnow)
    tx_hash = Column(String, nullable=True)


class SupportMessage(Base):
    __tablename__ = "support_messages"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    message = Column(Text)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True)
    value = Column(String)
