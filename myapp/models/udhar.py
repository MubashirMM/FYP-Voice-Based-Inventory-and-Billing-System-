from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, Float, String
from myapp.database.session import Base

class Udhar(Base):
    __tablename__ = "udhars"

    udhar_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer.customer_id"), unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)

    total_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unpaid")

    direct_addition: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    direct_deduction: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    customer = relationship("Customer", back_populates="udhar")
    user = relationship("User", back_populates="udhars")
