from fastapi import FastAPI, HTTPException
import redis
from celery.result import AsyncResult

from schema import WorkflowSchema
from tasks import schedule_task, celery_app

app = FastAPI()

@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.post("/schedule-workflow")
async def schedule_workflow(workflow: WorkflowSchema):
    try:
      print(f"Scheduling workflow: {workflow}")
      # JSON-serializable payload (datetimes -> ISO strings)
      payload = workflow.model_dump(mode="json")
      print(f"Payload: {payload}")
      ret = schedule_task.delay(payload)  # Example task call
      return {"message": "Workflow scheduled", "workflow": workflow, "task_id": ret.id}
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))


@app.get("/health/redis")
async def redis_health():
  """Check Redis connection used as Celery result backend."""
  try:
    # Match the Redis URL used by the Celery backend in tasks.py
    r = redis.Redis(host='localhost', port=6379, db=0, socket_connect_timeout=2)
    pong = r.ping()
    return {"redis": "ok"} if pong else HTTPException(status_code=500, detail="Redis ping failed")
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Redis error: {e}")


@app.get("/tasks/{task_id}")
async def get_task_result(task_id: str):
  """Retrieve Celery task status and result from the configured backend (Redis)."""
  try:
    async_result = AsyncResult(task_id, app=celery_app)
    status = async_result.status
    result = None
    if async_result.ready():
      result = async_result.result
    return {"task_id": task_id, "status": status, "result": result}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))