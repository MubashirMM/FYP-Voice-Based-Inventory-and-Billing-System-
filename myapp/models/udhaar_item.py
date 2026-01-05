
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import  ForeignKey, Float, Date,String
from datetime import date
from myapp.database.session import Base

class UdharItem(Base):
    __tablename__ = "udharitems"

    udharitem_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer.customer_id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("items.item_id"))
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)        
    requested_unit: Mapped[str] = mapped_column(String(20), nullable=False) 
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    date_: Mapped[date] = mapped_column(Date, default=date.today) 

    customer = relationship("Customer", back_populates="udharitems")
    item = relationship("Item", back_populates="udharitems")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    user = relationship("User", back_populates="udharitems")
