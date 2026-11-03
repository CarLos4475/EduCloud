import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    environment: str
    project: str
    emulators: bool
    pilot_uids: frozenset[str]
    pilot_emails: frozenset[str]

    @classmethod
    def load(cls):
        environment = os.getenv(
            "CAMPUS_ENV", "production" if os.getenv("K_SERVICE") else "local"
        )
        project = os.getenv("GOOGLE_CLOUD_PROJECT", "demo-campus")
        emulator_auth = os.getenv("FIREBASE_AUTH_EMULATOR_HOST")
        emulator_data = os.getenv("FIRESTORE_EMULATOR_HOST")
        if os.getenv("K_SERVICE") and (
            environment == "local"
            or project.startswith("demo-")
            or emulator_auth
            or emulator_data
        ):
            raise ValueError("Cloud Run no admite modo local ni emuladores.")
        if environment != "local" and (
            emulator_auth or emulator_data or project.startswith("demo-")
        ):
            raise ValueError("La configuración de emuladores solo es válida en local.")
        if environment == "local" and project.startswith("demo-"):
            emulator_auth = emulator_auth or "127.0.0.1:9099"
            emulator_data = emulator_data or "127.0.0.1:8080"
            os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = emulator_auth
            os.environ["FIRESTORE_EMULATOR_HOST"] = emulator_data
        for host in (emulator_auth, emulator_data):
            if host and host.split(":")[0] not in ("127.0.0.1", "localhost"):
                raise ValueError("Los emuladores deben estar en loopback.")
        if bool(emulator_auth) != bool(emulator_data):
            raise ValueError("Configura ambos emuladores o ninguno.")
        return cls(
            environment,
            project,
            bool(emulator_auth),
            frozenset(filter(None, os.getenv("CAMPUS_PILOT_UIDS", "").split(","))),
            frozenset(
                email.strip().lower()
                for email in os.getenv("CAMPUS_PILOT_EMAILS", "").split(",")
                if email.strip()
            ),
        )


def institutional_email(email: str) -> bool:
    return (
        email.strip().lower().endswith("@pcpuma.acatlan.unam.mx")
        and email.count("@") == 1
        and bool(email.split("@")[0].strip())
    )
