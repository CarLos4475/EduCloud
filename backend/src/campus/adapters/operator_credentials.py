"""Short-lived credentials for explicitly selected local cloud development."""

import os

from google.oauth2.credentials import Credentials


def local_operator_credentials(project: str):
    token = os.getenv("CAMPUS_LOCAL_ACCESS_TOKEN")
    if not token:
        return None
    if os.getenv("K_SERVICE"):
        raise ValueError("No se permiten credenciales de operador local en Cloud Run.")
    return Credentials(token, quota_project_id=project)
