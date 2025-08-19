import os
import logging
import requests
from datetime import date
from app.utility.hubspot import (
    get_deal_details_with_associations,
    get_objects_properties,
)

SERVICEM8_API_KEY = os.getenv("SERVICEM8_API_KEY")
HUBSPOT_API_TOKEN = os.getenv("HUBSPOT_API_TOKEN")
REQUIRED_DEAL_STAGE_ID = "953048614"


def create_servicem8_job(job_data):
    url = "https://api.servicem8.com/api_1.0/job.json"
    headers = {"X-Api-Key": SERVICEM8_API_KEY, "Content-Type": "application/json"}
    try:
        resp = requests.post(url, json=job_data, headers=headers)
        resp.raise_for_status()
        job_uuid = resp.headers.get("x-record-uuid")
        logging.info(f"Created ServiceM8 Job UUID: {job_uuid}")
        return job_uuid
    except Exception as e:
        logging.error(f"Error creating ServiceM8 job: {e}")
        return None


def create_servicem8_job_contact(job_uuid, contact):
    url = "https://api.servicem8.com/api_1.0/jobcontact.json"
    headers = {"X-Api-Key": SERVICEM8_API_KEY, "Content-Type": "application/json"}
    contact_payload = {
        "job_uuid": job_uuid,
        "first": contact.get("firstname"),
        "last": contact.get("lastname"),
        "phone": contact.get("phone"),
        "email": contact.get("email"),
        "type": "JOB",
        "is_primary_contact": 1,
    }
    try:
        resp = requests.post(url, json=contact_payload, headers=headers)
        resp.raise_for_status()
        logging.info(f"Created JobContact for job: {job_uuid}")
        return True
    except Exception as e:
        logging.error(f"Error creating JobContact: {e}")
        return False


def update_hubspot_deal_sm8_job_id(deal_id, job_uuid):
    url = f"https://api.hubapi.com/crm/v3/objects/deals/{deal_id}"
    headers = {
        "Authorization": f"Bearer {HUBSPOT_API_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {"properties": {"sm8_job_id": job_uuid}}
    try:
        resp = requests.patch(url, json=data, headers=headers)
        resp.raise_for_status()
        logging.info(f"Updated HubSpot deal {deal_id} with sm8_job_id: {job_uuid}")
        return True
    except Exception as e:
        logging.error(f"Error updating HubSpot deal {deal_id}: {e}")
        return False


def handle_create_job(event_data):
    """
    Handles the job creation process, now with a deal stage check.
    """
    deal_id = event_data.get("deal_record_id")
    if not deal_id:
        logging.error("No deal_record_id provided in the event data.")
        return

    details = get_deal_details_with_associations(deal_id)
    if not details:
        logging.error(f"Could not retrieve details for deal {deal_id}. Aborting.")
        return

    deal_details = get_objects_properties("deals", [deal_id], ["dealstage"])
    deal_stage = deal_details[0].get("properties", {})

    current_stage = deal_stage.get("dealstage")
    if current_stage != REQUIRED_DEAL_STAGE_ID:
        logging.warning(
            f"Skipping job creation for deal {deal_id}. "
            f"Stage '{current_stage}' does not match required stage '{REQUIRED_DEAL_STAGE_ID}'."
        )
        return

    logging.info(f"Deal {deal_id} is in the correct stage. Proceeding with job creation.")

    service_categories = event_data.get("service_categories", "")
    service_type = event_data.get("service_type", "")
    enquiry_notes = event_data.get("enquiry_notes", "")
    job_address = event_data.get("job_street_address", "")

    def format_value(label, value):
        items = [item.strip() for item in value.split(";") if item.strip()]
        return f"{label}: {', '.join(items)}" if items else f"{label}:"

    job_description = (
        f"{format_value('Service Category', service_categories)}\n"
        f"{format_value('Service Type', service_type)}\n"
        f"Enquiry Notes: {enquiry_notes.strip()}"
    )

    job_data = {
        "status": "Quote",
        "job_address": job_address,
        "job_description": job_description,
        "date": str(date.today()),
    }

    job_uuid = create_servicem8_job(job_data)
    if not job_uuid:
        return

    contact_data = {
        "firstname": details["contact"].get("firstname"),
        "lastname": details["contact"].get("lastname"),
        "phone": details["contact"].get("phone"),
        "email": details["contact"].get("email"),
    }

    create_servicem8_job_contact(job_uuid, contact_data)
    if deal_id:
        update_hubspot_deal_sm8_job_id(deal_id, job_uuid)
