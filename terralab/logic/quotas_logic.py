# logic/quotas_logic.py

import logging

from teaspoons_client import QuotasApi, QuotaWithDetails  # type: ignore[attr-defined]

from terralab.client import ClientWrapper

LOGGER = logging.getLogger(__name__)


def get_user_quota(pipeline_name: str) -> QuotaWithDetails:
    """Get the details of a user's quota for a specific pipeline"""
    with ClientWrapper() as api_client:
        quotas_client = QuotasApi(api_client=api_client)
        return quotas_client.get_quota_for_pipeline(pipeline_name=pipeline_name)
