# entrypoint for chatbot service
# exposes `app` object used by uvicorn

from api import app
from db import init_db

# make sure database tables exist
init_db()