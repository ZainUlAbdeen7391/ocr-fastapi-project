from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship
from Connections.database_connections import Base
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
    used_hits = Column(Integer, nullable=False)
    last_reset = Column(Date, nullable=False, default=date.today)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=pkt_now)
    api_end_date = Column(DateTime, default=lambda: pkt_now() + timedelta(days=30))
    
    # Relationship 
    user = relationship("User", back_populates="api_keys")

    @property
    def remaining_hits(self):
        return max(self.user.plan.monthly_hit_limit - self.used_hits, 0)


    @property
    def warning(self):
        """Progressive warning messages like GPT style."""
        remaining = self.remaining_hits
        if remaining == 3:
            return "⚠️ Only 3 hits remaining"
        elif remaining == 2:
            return "⚠️ Only 2 hits remaining"
        elif remaining == 1:
            return "⚠️ Last hit remaining"
        return None

    def is_expired(self):
        return pkt_now() > self.api_end_date

    def reset_if_new_month(self):
        today = date.today()
        if self.last_reset.month != today.month or self.last_reset.year != today.year:
            self.used_hits = 0
            self.last_reset = today

    def allow_hits(self, hits: int = 1):
        self.reset_if_new_month()
        return self.is_active and not self.is_expired() and self.remaining_hits >= hits

    def consume_hits(self, hits: int = 1):
        if self.allow_hits(hits):
            self.used_hits += hits
            return True
        return False
