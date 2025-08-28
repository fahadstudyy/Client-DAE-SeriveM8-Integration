import os
import logging
import requests
from datetime import datetime, timedelta, timezone
from app.utility.hubspot import (
    QUOTE_VIEWED_PIPELINE_ID,
    update_hubspot_deal_quote_viewed,
)

logging.basicConfig(level=logging.INFO)

SERVICEM8_API_KEY = os.getenv("SERVICEM8_API_KEY")
HUBSPOT_API_TOKEN = os.getenv("HUBSPOT_API_TOKEN")


def get_date_five_minutes_ago():
    return (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()


def fetch_recent_proposals(from_date):
    url = f"https://api.servicem8.com/api_1.0/proposal.json?$filter=last_viewed_timestamp gt '{from_date}'"
    headers = {"X-Api-Key": SERVICEM8_API_KEY, "accept": "application/json"}
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        proposals = resp.json()
        logging.info(f"Fetched {len(proposals)} proposals from ServiceM8.")
        return proposals
    except Exception as e:
        logging.error(f"Error fetching proposals: {e}")
        return []


def get_viewed_proposal_job_uuids(proposals):
    filtered_uuids = []
    for proposal in proposals:
        lvt = proposal.get("last_viewed_timestamp")
        if lvt and lvt != "0000-00-00 00:00:00":
            filtered_uuids.append(proposal.get("job_uuid"))
    logging.info(f"Found {len(filtered_uuids)} viewed proposals.")
    return filtered_uuids


def hubspot_batch_find_deals_by_job_ids(job_uuids):
    found = {}
    url = "https://api.hubapi.com/crm/v3/objects/deals/search"
    headers = {
        "Authorization": f"Bearer {HUBSPOT_API_TOKEN}",
        "Content-Type": "application/json",
    }
    chunk_size = 99
    for i in range(0, len(job_uuids), chunk_size):
        batch = job_uuids[i : i + chunk_size]
        filters = [{"propertyName": "sm8_job_id", "operator": "IN", "values": batch}]
        data = {
            "filterGroups": [{"filters": filters}],
            "properties": ["sm8_job_id", "sm8_quote_viewed"],
        }
        try:
            resp = requests.post(url, json=data, headers=headers)
            resp.raise_for_status()
            results = resp.json().get("results", [])
            for deal in results:
                properties = deal.get("properties", {})
                job_id = properties.get("sm8_job_id")

                # Get 'sm8_quote_viewed' and handle None case
                quote_viewed = properties.get("sm8_quote_viewed")
                if quote_viewed is not None:
                    quote_viewed = quote_viewed.lower()

                # Check if 'quote_viewed' is either 'false' or None
                if job_id and (quote_viewed == "false" or quote_viewed is None):
                    found[job_id] = deal["id"]
        except Exception as e:
            logging.error(f"Error searching deals in HubSpot: {e}")
    logging.info(f"Matched {len(found)} HubSpot deals with job_uuids.")
    return found


def update_deal_stages(deal_ids, new_stage):
    for deal_id in deal_ids:
        update_hubspot_deal_quote_viewed(deal_id, new_stage)


def cron_viewed_proposals_update_deal_stage(new_pipeline_stage):
    from_date = get_date_five_minutes_ago()
    proposals = fetch_recent_proposals(from_date)
    job_uuids = get_viewed_proposal_job_uuids(proposals)
    if not job_uuids:
        logging.info("No viewed proposals found.")
        return

    job_uuid_to_deal_id = hubspot_batch_find_deals_by_job_ids(job_uuids)
    if not job_uuid_to_deal_id:
        logging.info("No matching HubSpot deals found for viewed proposals.")
        return

    update_deal_stages(list(job_uuid_to_deal_id.values()), new_pipeline_stage)
    logging.info(
        f"Updated {len(job_uuid_to_deal_id)} HubSpot deals to new stage '{new_pipeline_stage}'."
    )


if __name__ == "__main__":
    cron_viewed_proposals_update_deal_stage(QUOTE_VIEWED_PIPELINE_ID)
