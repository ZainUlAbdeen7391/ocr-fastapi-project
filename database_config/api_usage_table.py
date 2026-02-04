from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date, DateTime
from configure_db import Base
from datetime import date, datetime, timedelta

def to_pkt(dt: datetime) -> str:
    return (dt + timedelta(hours=5)).isoformat()


def pkt_now():
    return datetime.utcnow() + timedelta(hours=5)


class APISummary(Base):
    __tablename__ = "api_keys"  

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("credentials.user_id"), nullable=False)

    api_key = Column(String(255), unique=True, nullable=False)

    monthly_limit = Column(Integer, nullable=False, default=5)
    used_hits = Column(Integer, nullable=False, default=0)

    last_reset = Column(Date, nullable=False, default=date.today)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, nullable=False, default=pkt_now)

    api_end_date = Column(DateTime, nullable=True, default=pkt_now)

    @property
    def remaining_hits(self) -> int:
        return max(self.monthly_limit - self.used_hits, 0)

    def is_expired(self) -> bool:
        if not self.api_end_date:
            return False
        return pkt_now() > self.api_end_date

    def allow_hits(self, hits: int = 1) -> bool:
        return (
            self.is_active
            and not self.is_expired()
            and self.remaining_hits >= hits
        )

    def consume_hits(self, hits: int = 1) -> bool:
        if self.allow_hits(hits):
            self.used_hits += hits
            return True
        return False    





