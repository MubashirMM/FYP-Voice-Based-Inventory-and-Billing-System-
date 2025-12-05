from myapp.database.session import Base
from sqlalchemy import String
from sqlalchemy.orm import Mapped,mapped_column,relationship

class Customer(Base):
    __tablename__="customer"
    customer_id:Mapped[int]=mapped_column(primary_key=True,index=True)
    customer_name:Mapped[str]=mapped_column(String(250),index=True)
    
    # models/customer.py
    sales = relationship("Sale", back_populates="customer")
    udharitems = relationship("UdharItem", back_populates="customer")
    udhar = relationship("Udhar", back_populates="customer", uselist=False)




