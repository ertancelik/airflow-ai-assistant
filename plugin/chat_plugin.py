from airflow.plugins_manager import AirflowPlugin
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

chat_app = FastAPI()

chat_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
chat_app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@chat_app.get("/", response_class=HTMLResponse)
async def chat_page():
    return """
    <html>
    <head>
        <link rel="stylesheet" href="/chat_plugin/static/chat.css">
    </head>
    <body>
        <h3>Airflow AI Assistant</h3>
        <script src="/chat_plugin/static/chat.js"></script>
    </body>
    </html>
    """

@chat_app.get("/inject", response_class=HTMLResponse)
async def inject():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Airflow AI Assistant</title>
    <link rel="stylesheet" href="/chat_plugin/static/chat.css">
    </head>
    <body>
    <script src="/chat_plugin/static/chat.js"></script>
    </body>
    </html>
    """

class AirflowChatPlugin(AirflowPlugin):
    name = "airflow_chat_plugin"
    fastapi_apps = [
        {
            "app": chat_app,
            "url_prefix": "/chat_plugin",
            "name": "Airflow Chat Plugin",
        }
    ]