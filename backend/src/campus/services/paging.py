import base64
import hashlib
import json

from campus.services.academic import DomainError


def page_rows(rows, uid, namespace, limit, cursor=None):
    scope = hashlib.sha256(f"{uid}:{namespace}".encode()).hexdigest()
    ordered = sorted(rows, key=lambda row: (row["createdAt"], row["id"]))
    if cursor:
        try:
            value = json.loads(base64.urlsafe_b64decode(cursor.encode()))
            if (
                value["scope"] != scope
                or not isinstance(value["after"], list)
                or len(value["after"]) != 2
            ):
                raise ValueError()
            after = tuple(value["after"])
            ordered = [row for row in ordered if (row["createdAt"], row["id"]) > after]
        except (ValueError, KeyError, TypeError):
            raise DomainError(
                422, "El cursor no corresponde a esta consulta."
            ) from None
    items = ordered[:limit]
    next_cursor = None
    if len(ordered) > limit:
        last = items[-1]
        next_cursor = base64.urlsafe_b64encode(
            json.dumps(
                {"scope": scope, "after": [last["createdAt"], last["id"]]}
            ).encode()
        ).decode()
    return {"items": items, "nextCursor": next_cursor}
