import json
from hashlib import sha256

from google.api_core.exceptions import AlreadyExists
from google.cloud.tasks_v2 import CloudTasksClient, HttpMethod

from campus.adapters.operator_credentials import local_operator_credentials


class CloudTaskQueue:
    def __init__(self, project, region, queue, worker_url, invoker_email):
        if not worker_url.startswith("https://"):
            raise ValueError("Worker URL must use HTTPS")
        self.client = CloudTasksClient(credentials=local_operator_credentials(project))
        self.parent = self.client.queue_path(project, region, queue)
        self.url, self.invoker = worker_url.rstrip("/"), invoker_email

    def enqueue(self, owner, job_id, dispatch_key="0"):
        name = f"{self.parent}/tasks/{sha256(f'{owner}:{job_id}:{dispatch_key}'.encode()).hexdigest()}"
        try:
            self.client.create_task(
                request={
                    "parent": self.parent,
                    "task": {
                        "name": name,
                        "http_request": {
                            "http_method": HttpMethod.POST,
                            "url": f"{self.url}/internal/jobs",
                            "headers": {"Content-Type": "application/json"},
                            "body": json.dumps(
                                {"ownerId": owner, "jobId": job_id}
                            ).encode(),
                            "oidc_token": {
                                "service_account_email": self.invoker,
                                "audience": self.url,
                            },
                        },
                    },
                }
            )
        except AlreadyExists:
            pass
