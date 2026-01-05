from myapp.database.session import Base
from sqlalchemy import String ,ForeignKey
from sqlalchemy.orm import Mapped,mapped_column,relationship

class Customer(Base):
    __tablename__="customer"
    customer_id:Mapped[int]=mapped_column(primary_key=True,index=True)
    customer_name:Mapped[str]=mapped_column(String(250),index=True,unique=True)
    
    udharitems = relationship("UdharItem", back_populates="customer")
    udhar = relationship("Udhar", back_populates="customer", uselist=False)


    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    # user = relationship("User", back_populates="customers")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    user = relationship("User", back_populates="customers")
    udhar = relationship("Udhar", back_populates="customer", uselist=False)




