from .job_activity import handle_job_activity
from .job import handle_job_quote_sent
from .create_job import handle_create_job


webhook_handlers = {
    "JobActivity": handle_job_activity,
    "Job": handle_job_quote_sent,
    "CreateJob": handle_create_job,
}
