from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint
from myapp.database.session import Base

class Customer(Base):
    __tablename__ = "customer"
    
    customer_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(250), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="customers")
    
    # ✅ FIXED: Change 'udhar' to 'udhars' to match the back_populates in Udhar model
    udhars = relationship("Udhar", back_populates="customer", cascade="all, delete-orphan")
    udharitems = relationship("UdharItem", back_populates="customer", cascade="all, delete-orphan")
    bills = relationship("Bill", back_populates="customer", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("customer_name", "user_id", name="uq_customer_name_per_user"),
    )