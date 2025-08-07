import os
import logging
import requests
from dotenv import load_dotenv
from app.utility.hubspot import (
    find_hubspot_deal_by_job_uuid,
    update_hubspot_deal_stage,
    ON_SITE_QUOTE_SCHEDULED_PIPELINE_ID,
)


load_dotenv()

SERVICEM8_API_KEY = os.getenv("SERVICEM8_API_KEY")
HUBSPOT_API_TOKEN = os.getenv("HUBSPOT_API_TOKEN")

def get_job_activity(uuid):
    url = f"https://api.servicem8.com/api_1.0/jobactivity/{uuid}.json"
    headers = {"accept": "application/json", "X-Api-Key": SERVICEM8_API_KEY}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Error fetching job activity: {e}")
        return None


def handle_job_activity(data):
    entry = data.get("entry", [{}])[0]
    job_activity_uuid = entry.get("uuid")
    if not job_activity_uuid:
        logging.error("No uuid in JobActivity entry.")
        return

    job_activity = get_job_activity(job_activity_uuid)
    if not job_activity:
        logging.error(f"Could not fetch JobActivity with uuid: {job_activity_uuid}")
        return

    if str(job_activity.get("activity_was_scheduled")) == "1":
        job_uuid = job_activity.get("job_uuid")
        if not job_uuid:
            logging.error("No job_uuid in JobActivity.")
            return

        deal_id = find_hubspot_deal_by_job_uuid(job_uuid)
        if deal_id:
            update_hubspot_deal_stage(deal_id, ON_SITE_QUOTE_SCHEDULED_PIPELINE_ID)
        else:
            logging.warning(f"No HubSpot deal found with sm8_job_uuid = {job_uuid}")
