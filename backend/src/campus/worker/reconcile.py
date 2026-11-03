"""One-shot outbox reconciler; invoke locally or from authenticated Scheduler."""

from campus.api.study_runtime import study_runtime
from campus.services.jobs import changed


def dispatch_pending(queue):
    state = study_runtime()
    count = 0
    for job in state.records.pending_jobs():
        if job["status"] in ("running", "cancel_requested"):
            job = state.jobs.recover_expired(job["ownerId"], job["id"])
            state.sync_failed_material(job)
        if job["status"] == "queued":
            outbox = state.records.get(job["ownerId"], "outbox", job["id"])
            if outbox and outbox["status"] == "pending":
                queue.enqueue(job["ownerId"], job["id"], f"attempt-{job['attempts']}")
                state.records.save(
                    job["ownerId"],
                    "outbox",
                    job["id"],
                    changed(outbox, status="dispatched"),
                    outbox["revision"],
                )
                count += 1
    return count
