from datetime import datetime, timezone
from typing import Optional, Dict, Any

from sqlalchemy import ForeignKey, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from myapp.database.session import Base

class Report(Base):
    __tablename__ = "reports"

    report_id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"),
        nullable=False
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)

    filters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    kpi_summary: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    table_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    charts_static: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    charts_interactive: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # relationship
    user: Mapped["User"] = relationship(back_populates="reports")
