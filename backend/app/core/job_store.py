"""
Job Store stub - minimal implementation.
"""


class JobStore:
    """Stub job store."""

    def __init__(self):
        self._jobs = {}

    def create(self, **kwargs):
        return None

    def get(self, job_id):
        return None
