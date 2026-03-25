from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, LargeBinary
from datetime import datetime, timezone
from myapp.database.session import Base
# from myapp.models.report import Report


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255))
    password_reset_code:Mapped[str]=mapped_column(String(255),nullable=True,default=None)
    password_reset_expiry: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    voice_embedding: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    udharitems = relationship("UdharItem", back_populates="user", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="user", cascade="all, delete-orphan")
    items = relationship("Item", back_populates="owner", cascade="all, delete-orphan")
    sales = relationship("Sale", back_populates="user", cascade="all, delete-orphan")
    udhars = relationship("Udhar", back_populates="user", cascade="all, delete-orphan")
    bills = relationship("Bill", back_populates="user", cascade="all, delete-orphan")
    bill_items = relationship("BillItemHistory", back_populates="user", cascade="all, delete-orphan")
    shops = relationship("Shop", back_populates="user", cascade="all, delete-orphan")
    billitems = relationship("BillItem", back_populates="user", cascade="all, delete-orphan")
    reports: Mapped[list["Report"]] = relationship(
    back_populates="user",
    cascade="all, delete-orphan"
)