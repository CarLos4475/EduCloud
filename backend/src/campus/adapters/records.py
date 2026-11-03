from contextvars import ContextVar
from copy import deepcopy
from threading import RLock
from typing import Any, Protocol


class Records(Protocol):
    def atomic(self, operation): ...
    def get(self, owner: str, collection: str, key: str) -> dict[str, Any] | None: ...
    def list(self, owner: str, collection: str) -> list[dict[str, Any]]: ...
    def save(
        self,
        owner: str,
        collection: str,
        key: str,
        value: dict[str, Any],
        expected: int | None,
    ) -> None: ...
    def remove(self, owner: str, collection: str, key: str) -> None: ...


class RevisionConflict(Exception):
    pass


class MemoryRecords:
    """Test adapter only; production startup never selects this adapter."""

    def __init__(self) -> None:
        self.data: dict[tuple[str, str, str], dict[str, Any]] = {}
        self.lock = RLock()

    def get(self, owner, collection, key):
        return deepcopy(self.data.get((owner, collection, key)))

    def atomic(self, operation):
        with self.lock:
            return operation()

    def list(self, owner, collection):
        return [
            deepcopy(v)
            for (o, c, _), v in self.data.items()
            if (o, c) == (owner, collection)
        ]

    def save(self, owner, collection, key, value, expected):
        with self.lock:
            current = self.get(owner, collection, key)
            if expected is not None and (
                not current or current["revision"] != expected
            ):
                raise RevisionConflict()
            self.data[(owner, collection, key)] = deepcopy(value)

    def remove(self, owner, collection, key):
        self.data.pop((owner, collection, key), None)


class FirestoreRecords:
    def __init__(self, project: str, credentials=None) -> None:
        from google.cloud import firestore

        from campus.adapters.operator_credentials import local_operator_credentials

        self.client = firestore.Client(
            project=project,
            credentials=credentials or local_operator_credentials(project),
        )
        self.context = ContextVar("firestore_transaction", default=None)

    def atomic(self, operation):
        from google.cloud import firestore

        transaction = self.client.transaction()

        @firestore.transactional
        def run(tx):
            token = self.context.set(tx)
            try:
                return operation()
            finally:
                self.context.reset(token)

        return run(transaction)

    def collection(self, owner, collection):
        return self.client.collection("users").document(owner).collection(collection)

    def get(self, owner, collection, key):
        snapshot = (
            self.collection(owner, collection)
            .document(key)
            .get(transaction=self.context.get())
        )
        return snapshot.to_dict() if snapshot.exists else None

    def list(self, owner, collection):
        return [
            snapshot.to_dict()
            for snapshot in self.collection(owner, collection)
            .limit(201)
            .stream(transaction=self.context.get())
        ]

    def save(self, owner, collection, key, value, expected):
        from google.cloud import firestore

        ref = self.collection(owner, collection).document(key)
        transaction = self.client.transaction()

        def write(tx):
            snapshot = ref.get(transaction=tx)
            if expected is None:
                if snapshot.exists:
                    raise RevisionConflict()
                tx.create(ref, value)
            else:
                if not snapshot.exists or snapshot.to_dict()["revision"] != expected:
                    raise RevisionConflict()
                tx.set(ref, value)

        current = self.context.get()
        if current is not None:
            write(current)
        else:
            firestore.transactional(write)(transaction)

    def remove(self, owner, collection, key):
        ref = self.collection(owner, collection).document(key)
        if self.context.get() is not None:
            self.context.get().delete(ref)
        else:
            ref.delete()
