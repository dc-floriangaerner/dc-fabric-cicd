# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Authentication helpers for Fabric deployment scripts."""

import os

from azure.identity import ClientSecretCredential, DefaultAzureCredential

from ..common.logger import get_logger
from .config import (
    ENV_AZURE_CLIENT_ID,
    ENV_AZURE_CLIENT_SECRET,
    ENV_AZURE_TENANT_ID,
    ENV_GITHUB_ACTIONS,
    WIKI_SETUP_GUIDE_URL,
    WIKI_TROUBLESHOOTING_URL,
)

logger = get_logger(__name__)

CredentialType = ClientSecretCredential | DefaultAzureCredential


def create_azure_credential() -> CredentialType:
    """Create and return the appropriate Azure credential based on environment.

    Raises:
        ValueError: If running in GitHub Actions but Service Principal secrets are not configured.
    """
    credentials = {
        ENV_AZURE_CLIENT_ID: os.getenv(ENV_AZURE_CLIENT_ID),
        ENV_AZURE_TENANT_ID: os.getenv(ENV_AZURE_TENANT_ID),
        ENV_AZURE_CLIENT_SECRET: os.getenv(ENV_AZURE_CLIENT_SECRET),
    }
    missing_vars = [name for name, value in credentials.items() if not value]
    provided_vars = [name for name, value in credentials.items() if value]

    if not missing_vars:
        client_id = credentials[ENV_AZURE_CLIENT_ID]
        tenant_id = credentials[ENV_AZURE_TENANT_ID]
        client_secret = credentials[ENV_AZURE_CLIENT_SECRET]
        assert client_id is not None and tenant_id is not None and client_secret is not None

        logger.info("-> Using ClientSecretCredential for authentication")
        return ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
        )

    is_ci = os.getenv(ENV_GITHUB_ACTIONS, "").lower() == "true"

    if is_ci or provided_vars:
        if provided_vars:
            hint = (
                f"The following secrets are set but incomplete — missing: {', '.join(missing_vars)}. "
                "All three must be configured together."
            )
        else:
            hint = (
                f"None of the required GitHub secrets are configured: "
                f"{ENV_AZURE_CLIENT_ID}, {ENV_AZURE_TENANT_ID}, {ENV_AZURE_CLIENT_SECRET}."
            )
        raise ValueError(
            f"{hint}\n"
            "\n"
            "  These secrets authenticate the deployment pipeline to Microsoft Fabric\n"
            "  using a Service Principal (Entra ID App Registration).\n"
            "\n"
            f"  Setup instructions : {WIKI_SETUP_GUIDE_URL}\n"
            f"  Troubleshooting    : {WIKI_TROUBLESHOOTING_URL}#clientsecretcredential-authentication-failed\n"
        )

    logger.info("-> Using DefaultAzureCredential for authentication (local development)")
    return DefaultAzureCredential()
