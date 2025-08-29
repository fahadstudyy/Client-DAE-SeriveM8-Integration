import os
import logging
import requests

SERVICEM8_API_KEY = os.getenv("SERVICEM8_API_KEY")


def update_job_to_unsuccessfull(uuid):
    url = f"https://api.servicem8.com/api_1.0/job/{uuid}.json"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "X-Api-Key": SERVICEM8_API_KEY,
    }
    payload = {"status": "Unsuccessful"}

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        logging.info(f"Successfully updated job {uuid} to Work Order.")
        return response.json()
    except Exception as e:
        logging.error(f"Error updating job {uuid} to Work Order: {e}")
        return None
