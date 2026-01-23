import os
from functools import cache
from pathlib import Path

from benchling_sdk.apps.framework import App
from benchling_sdk.auth.client_credentials_oauth2 import ClientCredentialsOAuth2
from benchling_sdk.benchling import Benchling
from benchling_sdk.models.webhooks.v0 import WebhookEnvelopeV0


def init_app_from_webhook(webhook: WebhookEnvelopeV0) -> App:
    return App(webhook.app.id, _benchling_from_webhook(webhook))


@cache
def app_definition_id() -> str:
    # App definition ID is available to "global" apps. It uniquely identifies the Benchling App
    # above the tenant context.
    #
    # Although it is available via the webhook, for security purposes we choose to supply it with
    # the App's code to avoid reusing elements of the webhook's data payload as part of its verification.
    # For ease of setup, we retrieve it from an environment variable.
    # You could choose to simply leave it in code like `return "appdef_SpzX0d5oDA"`.
    app_def_id = os.environ.get("BENCHLING_APP_DEFINITION_ID")
    assert app_def_id is not None, "Missing APP_DEFINITION_ID from environment"
    return app_def_id


def _benchling_from_webhook(webhook: WebhookEnvelopeV0) -> Benchling:
    return Benchling(webhook.base_url, _auth_method())


@cache
def _auth_method() -> ClientCredentialsOAuth2:
    client_id = os.environ.get("BENCHLING_CLIENT_ID")
    assert client_id is not None, "Missing BENCHLING_CLIENT_ID from environment"
    client_secret = os.environ.get('BENCHLING_CLIENT_SECRET')
    assert client_secret is not None, "Missing BENCHLING_CLIENT_SECRET from environment"
    return ClientCredentialsOAuth2(client_id, client_secret)
