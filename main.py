import uvicorn
from app.app import app

if __name__ == "__main__":
    # Point uvicorn to the app instance inside app/app.py
    uvicorn.run("app.app:app", host="127.0.0.1", port=8000, reload=True)
