# models/report.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, DateTime, String, Text
from datetime import datetime
from myapp.database.session import Base

class Report(Base):
    __tablename__ = "reports"

    report_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    item_name: Mapped[str] = mapped_column(String(100), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    filters_applied: Mapped[str] = mapped_column(Text, nullable=True)

    kpi_summary: Mapped[str] = mapped_column(Text, nullable=True)   # JSON string of KPIs
    charts_paths: Mapped[str] = mapped_column(Text, nullable=True)  # folder path for charts

    user = relationship("User", back_populates="reports")
