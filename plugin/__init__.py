from airflow.plugins_manager import AirflowPlugin
from flask import Blueprint
import os

chat_blueprint = Blueprint(
    "chat_plugin",
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
    static_url_path="/static/chat_plugin"
)

class AirflowChatPlugin(AirflowPlugin):
    name = "airflow_chat_plugin"
    flask_blueprints = [chat_blueprint]

    def on_load(self, *args, **kwargs):
        pass