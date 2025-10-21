from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class WorkflowSchema(BaseModel):
  workflow_id: Optional[str] = None
  owner_id: str
  name: str
  query: str
  start_time_utc: datetime
  interval_seconds: int
  active: bool = True
  next_run_at_utc: Optional[datetime] = None
  next_run_id: Optional[str] = None
  last_result: Optional[str] = None
  last_run_at_utc: Optional[datetime] = None
  created_at: Optional[datetime] = None

class UserSchema(BaseModel):
  uid: str
  email: Optional[str] = None
  display_name: Optional[str] = None
  workflows_created: int = 0
  created_at: Optional[datetime] = None

class TaskSchema(BaseModel):
  task_id: Optional[str] = None
  workflow_id: str
  owner_id: str
  status: str
  result: Optional[str] = None
  scheduled_run_at: Optional[datetime] = None
  created_at: Optional[datetime] = None
  completed_at: Optional[datetime] = None