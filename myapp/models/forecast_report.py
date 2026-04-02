# myapp/models/forecast_report.py
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from myapp.database.session import Base

class ForecastReport(Base):
    __tablename__ = "forecast_reports"
    
    id = Column(String(50), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    period_type = Column(String(20), nullable=False)  # weekly or monthly
    forecast_days = Column(Integer, default=30)
    total_items_analyzed = Column(Integer, default=0)
    increasing_count = Column(Integer, default=0)
    decreasing_count = Column(Integer, default=0)
    stable_count = Column(Integer, default=0)
    pdf_path = Column(String(500), nullable=True)
    excel_path = Column(String(500), nullable=True)
    csv_path = Column(String(500), nullable=True)
    folder_path = Column(String(500), nullable=True)
    status = Column(String(20), default="processing")  # processing, completed, failed
    error_message = Column(Text, nullable=True)
    generated_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationship with User - make sure back_populates matches User model
    user = relationship("User", back_populates="forecast_reports")
    
    # Add indexes for better performance
    __table_args__ = (
        Index('idx_forecast_reports_user_id', 'user_id'),
        Index('idx_forecast_reports_status', 'status'),
    )

    def __repr__(self):
        return f"<ForecastReport {self.id} by user {self.user_id}>"