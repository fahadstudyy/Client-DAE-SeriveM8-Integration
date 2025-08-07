import os
import logging
import requests
from dotenv import load_dotenv
from app.utility.hubspot import (
    find_hubspot_deal_by_job_uuid,
    update_hubspot_deal_stage,
    QUOTE_SENT_UNOPEN_PIPELINE_ID,
)

load_dotenv()

SERVICEM8_API_KEY = os.getenv("SERVICEM8_API_KEY")
HUBSPOT_API_TOKEN = os.getenv("HUBSPOT_API_TOKEN")


def get_job(uuid):
    url = f"https://api.servicem8.com/api_1.0/job/{uuid}.json"
    headers = {"accept": "application/json", "X-Api-Key": SERVICEM8_API_KEY}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Error fetching job: {e}")
        return None


def handle_job_quote_sent(data):
    entry = data.get("entry", [{}])[0]
    job_uuid = entry.get("uuid")
    if not job_uuid:
        logging.error("No uuid in Job entry.")
        return

    job = get_job(job_uuid)
    if not job:
        logging.error(f"Could not fetch Job with uuid: {job_uuid}")
        return

    if job.get("quote_sent") is True:
        deal_id = find_hubspot_deal_by_job_uuid(job_uuid)
        if deal_id:
            update_hubspot_deal_stage(deal_id, QUOTE_SENT_UNOPEN_PIPELINE_ID)
        else:
            logging.warning(f"No HubSpot deal found with sm8_job_uuid = {job_uuid}")
    else:
        logging.info("Quote not sent yet for this job.")
