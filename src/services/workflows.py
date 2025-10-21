from src.services.firebase_client import get_user_ref, get_workflow_ref
from firebase_admin import firestore

def pause_workflow(user_id: str, workflow_id: str):
    print("Pausing workflow:", workflow_id)
    workflow_ref = get_workflow_ref(user_id, workflow_id)
    snap = workflow_ref.get()
    
    if not snap.exists:
        raise Exception("Workflow not found")
    
    workflow_data = snap.to_dict()
    if not workflow_data.get("active", True):
        print("Workflow is already inactive")
        return 
    
    workflow_ref.update({
        "active": False,
        "next_run_at_utc": None,
        "next_run_id": None
    })
    
    print(f"Workflow {workflow_id} stopped successfully")

def delete_workflow(user_id: str, workflow_id: str):
    print("Deleting workflow:", workflow_id)
    workflow_ref = get_workflow_ref(user_id, workflow_id)
    user_ref = get_user_ref(user_id)
    snap = workflow_ref.get()
    
    if not snap.exists:
        raise Exception("Workflow not found")
    
    # Delete all tasks associated with the workflow
    tasks = workflow_ref.collection("tasks").stream()
    for task in tasks:
        task.reference.delete()
    
    # Delete the workflow itself
    workflow_ref.delete()
    
    print(f"Workflow {workflow_id} and its tasks deleted successfully")

    user_ref.update({
        "workflows_created": firestore.Increment(-1)
    })

def add_workflow(user_uid: str, workflow_data: dict):
    workflow_data['created_at'] = firestore.SERVER_TIMESTAMP
    user_ref = get_user_ref(user_uid)
    workflows_collection = user_ref.collection("workflows")
    
    # Add a new document with a generated ID
    write_time, workflow_ref = workflows_collection.add(workflow_data)

    workflow_ref.update({"workflow_id": workflow_ref.id})

    print("Added workflow to Firestore")

    user_ref.update({
        "workflows_created": firestore.Increment(1)
    })

    return workflow_ref