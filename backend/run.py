import os
import sys
import uvicorn

# Append current folder and app folder to system paths
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))
sys.path.append(os.path.dirname(__file__))

from app.config import settings

if __name__ == "__main__":
    print("-------------------------------------------------------------")
    print(f"Launching SentiScrapper Financial API on {settings.HOST}:{settings.PORT}")
    print("-------------------------------------------------------------")
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
