from typing import Any
from fastapi import Depends, FastAPI, HTTPException
import redis
from celery.result import AsyncResult

from src.schema import UserSchema, WorkflowSchema
from src.services.workflows import add_workflow, pause_workflow, delete_workflow
from src.tasks import schedule_task, celery_app

from src.services.auth import get_current_user

app = FastAPI()

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.post("create-user")
async def create_user(user_details: UserSchema, user: dict[str: Any] = Depends(get_current_user)):
    try:
        if not user or user.get("uid") is None:
          raise HTTPException(status_code=401, detail="Unauthorized")
        
        print(f"Creating user: {user_details}")
        # Here you would typically save the user to your database
        return {"message": "User created", "user": user_details.model_dump(mode="json")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
   

@app.post("/workflows/add")
async def add_workflow_endpoint(workflow: WorkflowSchema, user: dict[str: Any] = Depends(get_current_user)):
    try:
      if not user or user.get("uid") is None:
          raise HTTPException(status_code=401, detail="Unauthorized")
      if user.get("uid") != workflow.owner_id:
          raise HTTPException(status_code=403, detail="Forbidden: The authenticated user does not match the workflow owner.")
      
      print("Adding workflow to user DB")
      workflow_ref = add_workflow(workflow.owner_id, workflow.model_dump())
      print(f"Workflow added to db with ID: {workflow_ref.id}")
      
      print(f"Scheduling workflow: {workflow}")

      ret = schedule_task.delay(workflow.owner_id, workflow_ref.id)

      return {"message": "Workflow scheduled", "workflow": workflow.model_dump(mode="json"), "task_id": ret.id}
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))


@app.post("/workflows/{workflow_id}/pause")
async def pause_workflow_endpoint(workflow_id: str, user: dict[str: Any] = Depends(get_current_user)):
    try:
      if not user or user.get("uid") is None:
          raise HTTPException(status_code=401, detail="Unauthorized")
      user_uid = user.get("uid")
      print(f"Pausing workflow {workflow_id} for user {user_uid}")
      pause_workflow(user_uid, workflow_id)
      return {"message": "Workflow stopped", "workflow_id": workflow_id}
    except Exception as e:
      print(str(e))
      raise HTTPException(status_code=500, detail=str(e))


@app.delete("/workflows/{workflow_id}/delete")
async def delete_workflow_endpoint(workflow_id: str, user: dict[str: Any] = Depends(get_current_user)):
    try:
      if not user or user.get("uid") is None:
          raise HTTPException(status_code=401, detail="Unauthorized")
      user_uid = user.get("uid")
      delete_workflow(user_uid, workflow_id)
      return {"message": "Workflow deleted", "workflow_id": workflow_id}
    except Exception as e:
      print(str(e))
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