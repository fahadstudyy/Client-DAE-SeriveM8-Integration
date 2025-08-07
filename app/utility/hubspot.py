import os
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

HUBSPOT_API_TOKEN = os.getenv("HUBSPOT_API_TOKEN")

ON_SITE_QUOTE_SCHEDULED_PIPELINE_ID = "1690811882"
QUOTE_SENT_UNOPEN_PIPELINE_ID = "1690215923"
QUOTE_VIEWED_PIPELINE_ID = "1690215924"
CUSTOM_JOB_OBJECT_ID = "2-36823346"

def find_hubspot_deal_by_job_uuid(job_uuid):
    url = "https://api.hubapi.com/crm/v3/objects/deals/search"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {HUBSPOT_API_TOKEN}",
    }
    payload = {
        "filterGroups": [
            {
                "filters": [
                    {
                        "propertyName": "sm8_job_id",
                        "operator": "EQ",
                        "value": job_uuid,
                    }
                ]
            }
        ],
        "properties": ["dealstage"],
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        results = response.json().get("results", [])
        if results:
            return results[0].get("id")
        return None
    except Exception as e:
        logging.error(f"Error searching HubSpot deal: {e}")
        return None


def update_hubspot_deal_stage(deal_id, new_stage):
    url = f"https://api.hubapi.com/crm/v3/objects/deals/{deal_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {HUBSPOT_API_TOKEN}",
    }
    payload = {"properties": {"dealstage": new_stage}}
    try:
        response = requests.patch(url, headers=headers, json=payload)
        response.raise_for_status()
        logging.info(
            f"Successfully updated HubSpot deal {deal_id} to stage {new_stage}"
        )
        return True
    except Exception as e:
        logging.error(f"Error updating HubSpot deal: {e}")
        return False

def get_associated_ids(from_object, from_id, to_object):
    url = f"https://api.hubapi.com/crm/v4/objects/{from_object}/{from_id}/associations/{to_object}"
    headers = {"Authorization": f"Bearer {HUBSPOT_API_TOKEN}"}
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        # Return a list of associated IDs
        return [item["toObjectId"] for item in results]
    except Exception as e:
        logging.error(f"Error getting associations from {from_object} {from_id} to {to_object}: {e}")
        return []
    

def get_objects_properties(object_type, object_ids, properties):
    url = f"https://api.hubapi.com/crm/v3/objects/{object_type}/batch/read"
    headers = {"Authorization": f"Bearer {HUBSPOT_API_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "properties": properties,
        "inputs": [{"id": obj_id} for obj_id in object_ids]
    }
    try:
        resp = requests.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        # Return the list of result objects with their properties
        return resp.json().get("results", [])
    except Exception as e:
        logging.error(f"Error batch reading {object_type}: {e}")
        return []
    
def get_deal_details_with_associations(deal_id):

    contact_ids = get_associated_ids("deals", deal_id, "contacts")
    if not contact_ids:
        logging.warning(f"Aborting: No contacts associated with deal {deal_id}")
        return None
    
    job_object_ids = get_associated_ids("deals", deal_id, CUSTOM_JOB_OBJECT_ID)
    if not job_object_ids:
        logging.warning(f"Aborting: No custom job objects associated with deal {deal_id}")
        return None

    contact_props = ["firstname", "lastname", "email", "phone"]
    contacts = get_objects_properties("contacts", [contact_ids[0]], contact_props)
    
    job_props = ["job_address", "job_description"]
    job_objects = get_objects_properties(CUSTOM_JOB_OBJECT_ID, [job_object_ids[0]], job_props)

    if not contacts or not job_objects:
        logging.error(f"Aborting: Failed to fetch properties for objects associated with deal {deal_id}")
        return None

    details = {
        "contact": contacts[0].get("properties", {}),
        "job": job_objects[0].get("properties", {})
    }
    return details
