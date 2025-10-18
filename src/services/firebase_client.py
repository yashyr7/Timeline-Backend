import os
import logging
import firebase_admin
from firebase_admin import credentials, firestore, auth as firebase_auth
from dotenv import load_dotenv

from src.schema import UserSchema

logger = logging.getLogger(__name__)
load_dotenv()

firebase_service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_service_account_path)
    firebase_admin.initialize_app(cred)

db = firestore.client()
auth = firebase_auth

def create_new_user(user: UserSchema):
    user_dict = user.model_dump()
    user_dict['created_at'] = firestore.SERVER_TIMESTAMP
    db.collection("users").document(user.uid).set(user_dict)
    user_ref = db.collection("users").document(user.uid)
    return user_ref
    

def get_firestore_client():
    return db

def get_auth_client():
    return auth

def get_user_ref(user_uid: str):
    return db.collection("users").document(user_uid)

def get_workflow_ref(user_uid: str, workflow_id: str):
    return db.collection("users").document(user_uid).collection("workflows").document(workflow_id)

def add_workflow_to_user_db(user_uid: str, workflow_data: dict):
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
