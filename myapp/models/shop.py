from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey
from myapp.database.session import Base

class Shop(Base):
    __tablename__ = "shops"

    shop_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    shop_name: Mapped[str] = mapped_column(String(250), nullable=False, index=True)
    address: Mapped[str] = mapped_column(String(500), nullable=True)

    # User scoping
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    user = relationship("User", back_populates="shops")

