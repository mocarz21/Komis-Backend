import uvicorn
from fastapi import FastAPI, Request, HTTPException
from starlette.middleware import Middleware
from fastapi.responses import FileResponse
import os
import yaml
from jose import jwt, JWTError
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from database import db, lifespan
from routes import router


with open("settings.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
    

SECRET_KEY  = config['global']['security']['secret_key']
ALGORITHM   = config['global']['security']['algorithm']
UI_FOLDER = "ui"
UI_PATH = os.path.join(os.getcwd(), UI_FOLDER)

app = FastAPI(lifespan = lifespan)
app.include_router(router)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",   
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=7474, log_level="info")