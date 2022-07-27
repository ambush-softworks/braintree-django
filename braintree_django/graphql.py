from base64 import b64encode

from django.conf import settings

from gql import Client
from gql.transport.aiohttp import AIOHTTPTransport

from .settings import braintree_settings


class BraintreeGraphQL:
    def __init__(self):
        base64_token = b64encode('{}:{}'.format(
            braintree_settings.BRAINTREE_PUBLIC_KEY,
            braintree_settings.BRAINTREE_PRIVATE_KEY
        ).encode('utf-8'))
        api_token = str(base64_token, "utf-8")

        headers = {
            'Authorization': "Basic {}".format(api_token),
            'Braintree-Version': '2022-07-19',
            'Content-Type': 'application/json'
        }

        if settings.DEBUG == False:
            transport = AIOHTTPTransport(
                url=braintree_settings.BRAINTREE_PRODUCTION_URL,
                headers=headers
            )
        else:
            transport = AIOHTTPTransport(
                url=braintree_settings.BRAINTREE_SANDBOX_URL,
                headers=headers
            )

        self._client = Client(
            transport=transport,
            fetch_schema_from_transport=False
        )
