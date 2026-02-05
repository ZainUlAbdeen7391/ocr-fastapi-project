from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship
from configure_db import Base
from datetime import date, datetime, timedelta


def pkt_now():
    return datetime.utcnow() + timedelta(hours=5)

def to_pkt(dt: datetime) -> str: 
    return (dt + timedelta(hours=5)).isoformat()

class APISummary(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("credentials.user_id"), nullable=False)

    api_key = Column(String(255), unique=True, nullable=False)

    monthly_limit = Column(Integer, nullable=False, default=2)
    used_hits = Column(Integer, nullable=False, default=0)

    last_reset = Column(Date, nullable=False, default=date.today)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, nullable=False, default=pkt_now)

    api_end_date = Column(DateTime, default=lambda: pkt_now() + timedelta(days=30))

    user = relationship("User", back_populates="api_keys")

    @property
    def remaining_hits(self):
        return max(self.monthly_limit - self.used_hits, 0)

    def is_expired(self):
        return pkt_now() > self.api_end_date

    def reset_if_new_month(self):
        today = date.today()
        if self.last_reset.month != today.month:
            self.used_hits = 0
            self.last_reset = today

    def allow_hits(self, hits: int = 1):
        self.reset_if_new_month()

        return (
            self.is_active
            and not self.is_expired()
            and self.remaining_hits >= hits
        )

    def consume_hits(self, hits: int = 1):
        if self.allow_hits(hits):
            self.used_hits += hits
            return True
        return False
