from datetime import datetime, timezone
from celery import Celery
from schema import WorkflowSchema
from utils import calculate_next_run

celery_app = Celery('tasks', broker='amqp://timeline:timeline@localhost:5672/timelinehost', backend='redis://localhost:6379/0')


@celery_app.task
def schedule_task(payload: dict):
    
    try:
        workflow = WorkflowSchema.model_validate(payload)
        print(f"Scheduling workflow: {workflow}")
        print(f"Workflow last_run_at_utc: {workflow.last_run_at_utc}")
        result = "Expample response from LLM API for query: " + workflow.query
        now_utc = datetime.now(timezone.utc)
        next_run_time = calculate_next_run(workflow.start_time_utc, workflow.interval_seconds, from_time=now_utc)
        workflow.last_result = result
        workflow.last_run_at_utc = workflow.next_run_at_utc
        workflow.next_run_at_utc = next_run_time
        celery_payload = workflow.model_dump()
        schedule_task.apply_async((celery_payload,), eta=next_run_time)
        return result
    except Exception as e:
        print(f"Error scheduling workflow: {e}")
        return {"error": str(e)}