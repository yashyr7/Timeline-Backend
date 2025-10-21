from datetime import datetime, timezone
from celery import Celery
from src.schema import TaskSchema, WorkflowSchema
from src.services.firebase_client import get_workflow_ref
from src.utils import calculate_next_run

celery_app = Celery('tasks', broker='amqp://timeline:timeline@localhost:5672/timelinehost', backend='redis://localhost:6379/0')


@celery_app.task(bind=True)
def schedule_task(self, user_id: str = None, workflow_id: str = None):
    
    try:
        
        workflow_ref = get_workflow_ref(user_id, workflow_id)

        print("Fetching workflow data from Firestore")
        snap = workflow_ref.get()
        if not snap.exists:
            return {"error": "workflow_not_found", "workflow_id": workflow_id}

        workflow_data = snap.to_dict()
        workflow = WorkflowSchema.model_validate(workflow_data)

        print(f"Fetching response for workflow query: {workflow.query}")

        result = "Expample response from LLM API for query: " + workflow.query
        now_utc = datetime.now(timezone.utc)

        current_task_id = getattr(self.request, "id", None)

        # Create a Task entry for the first run
        if workflow.last_result is None:
            result = result
            task: TaskSchema = TaskSchema(
                task_id=current_task_id,
                workflow_id=workflow_id,
                owner_id=user_id,
                status="COMPLETED",
                result=result,
                scheduled_run_at=now_utc,
                created_at=now_utc,
                completed_at=now_utc
            )
            workflow_ref.collection("tasks").document(task.task_id).set(task.model_dump())
            workflow.next_run_at_utc = now_utc
        else:
            # Update the current task entry
            task_ref = workflow_ref.collection("tasks").document(current_task_id)
            task_ref.update({
                "status": "COMPLETED",
                "result": result,
                "completed_at": now_utc
            })
        
        next_run_time = calculate_next_run(workflow.start_time_utc, workflow.interval_seconds, from_time=now_utc)
        
        next_task_id = None
        if workflow.active:
            next_task_async = schedule_task.apply_async((user_id, workflow_id), eta=next_run_time)
            next_task_id = next_task_async.id

            next_task: TaskSchema = TaskSchema(
                task_id=next_task_id,
                workflow_id=workflow_id,
                owner_id=user_id,
                status="SCHEDULED",
                scheduled_run_at=next_run_time,
                created_at=now_utc
            )

            workflow_ref.collection("tasks").document(next_task.task_id).set(next_task.model_dump())
        
        workflow_ref.update({
            "last_result": result, 
            "last_run_at_utc": workflow.next_run_at_utc, 
            "next_run_at_utc": next_run_time if next_task_id else None, 
            "next_run_id": next_task_async.id
        })
                        
        return {
            "status": "ok",
            "workflow_id": workflow_id,
            "user_id": user_id,
            "completed_task_id": current_task_id,
            "next_task_id": next_task_id,
        }
    except Exception as e:
        print(f"Error scheduling workflow: {e}")
        return {"error": str(e)}