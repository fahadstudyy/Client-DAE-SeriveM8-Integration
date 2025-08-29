import os
import logging
from dotenv import load_dotenv
from app.utility.job import update_job_to_unsuccessfull

load_dotenv()

SERVICEM8_API_KEY = os.getenv("SERVICEM8_API_KEY")


def handle_lost_job(data):
    job_uuid = data.get("uuid")
    if not job_uuid:
        logging.error("No uuid in Job entry.")
        return

    update_job_to_unsuccessfull(job_uuid)
