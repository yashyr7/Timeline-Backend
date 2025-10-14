from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class WorkflowSchema(BaseModel):
  #id: Optional[int]
  name: str
  query: str
  start_time_utc: datetime
  interval_seconds: int
  active: bool = True
  next_run_at_utc: Optional[datetime] = None
  last_result: Optional[str] = None
  last_run_at_utc: Optional[datetime] = None