from functools import lru_cache

import firebase_admin
from fastapi import Header
from firebase_admin import auth
from firebase_admin.exceptions import FirebaseError

from campus.adapters.operator_credentials import local_operator_credentials
from campus.adapters.records import FirestoreRecords
from campus.config import Settings, institutional_email
from campus.domain.contracts import Actor
from campus.services.academic import AcademicService, DomainError


@lru_cache
def settings():
    return Settings.load()


@lru_cache
def firebase_app():
    try:
        return firebase_admin.get_app()
    except ValueError:
        credential = local_operator_credentials(settings().project)
        if credential is not None:
            from firebase_admin.credentials import Base

            class OperatorCredential(Base):
                def get_credential(self):
                    return credential

            return firebase_admin.initialize_app(
                OperatorCredential(), options={"projectId": settings().project}
            )
        return firebase_admin.initialize_app(options={"projectId": settings().project})


def current_actor(authorization: str | None = Header(default=None)) -> Actor:
    if (
        not authorization
        or not authorization.startswith("Bearer ")
        or len(authorization) > 8192
    ):
        raise DomainError(401, "Inicia sesión para continuar.")
    try:
        claims = auth.verify_id_token(
            authorization[7:], app=firebase_app(), check_revoked=True
        )
    except (ValueError, FirebaseError):
        raise DomainError(401, "La sesión no es válida o ha expirado.") from None
    config = settings()
    email = claims.get("email", "")
    if not institutional_email(email):
        raise DomainError(403, "Usa tu correo @pcpuma.acatlan.unam.mx.")
    if not config.emulators and not claims.get("email_verified", False):
        raise DomainError(403, "Verifica tu correo institucional antes de continuar.")
    if (
        not config.emulators
        and claims["uid"] not in config.pilot_uids
        and email.lower() not in config.pilot_emails
    ):
        raise DomainError(403, "Esta cuenta no está habilitada para el piloto.")
    return Actor(uid=claims["uid"], pilot_enabled=True)


@lru_cache
def academic_service():
    return AcademicService(FirestoreRecords(settings().project))
