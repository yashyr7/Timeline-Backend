from typing import Any
from fastapi import Depends, HTTPException, status, Request
from firebase_admin import auth

def get_bearer_token(request: Request) -> str:
  auth_header = request.headers.get("Authorization")
  if not auth_header or not auth_header.lower().startswith("bearer "):
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid Authorization header",
    )
  return auth_header.split(" ", 1)[1].strip()

def get_current_user(token: str = Depends(get_bearer_token)) -> dict[str: Any]:
  try:
    decoded = auth.verify_id_token(token)

    return decoded
  except Exception as e:
    print("get_current_user error:", e)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"Invalid ID token: {str(e)}",
    )
    
