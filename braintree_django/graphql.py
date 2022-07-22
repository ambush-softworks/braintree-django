import json
from base64 import b64encode
from dataclasses import dataclass
from typing import Dict
from django.conf import settings

from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

from .settings import braintree_settings


@dataclass
class BraintreePaymentMethod:
    payment_method: Dict
    verification: Dict

    def __init__(self, result: Dict):
        self.payment_method = data.vaultPaymentMethod.payment_method
        self.verification = data.vaultPaymentMethod.verification

    def id(self) -> str:
        return self.payment_method.id


@dataclass
class BraintreeCustomer:
    def __init__(self, id: str = None, company_name: str = None, first_name: str = None, last_name: str = None):
        self.id = id
        self.company_name = company_name
        self.first_name = first_name
        self.last_name = last_name

    def to_json(self):
        data = {}
        if self.company_name:
            data.update(
                {"company": self.company_name}
            )
        if self.first_name:
            data.update(
                {"firstName": self.first_name}
            )
        if self.last_name:
            data.update(
                {"lastName": self.last_name}
            )
        return json.dumps(data)

    def create(self):
        result = create_customer(self)
        self.id = get_id(result)

    def get_id(self, result) -> str:
        """
        Parses result and returns customer id
        """
        try:
            customer_data = json.loads(
                result)["data"]["createCustomer"]["customer"]
            self.id = customer_data["id"]
            return self.id
        except:
            return None


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

    def client_token(self):
        query = gql(
            """
            mutation ClientToken($merchant: CreateClientTokenInput) {
                createClientToken(input: $merchant) {
                    clientToken
                }
            }
            """
        )
        params = {
            "merchant": {
                "clientToken": {
                    "merchantAccountId": braintree_settings.BRAINTREE_MERCHANT_ID,
                    "customerId": 4
                }
            }
        }

        result = self._client.execute(query, variable_values=params)

        return result

    def create_customer(self, customer: BraintreeCustomer = None):
        query = gql(
            """
            mutation CreateCustomer($input: CreateCustomerInput!) {
                createCustomer(input: $input) {
                    customer {
                    id
                    company
                    firstName
                    lastName
                    }
                }
            }
            """
        )
        params = {
            "input": {
                "customer": {
                    customer.to_json()
                }
            }
        }
        result = self._client.execute(query, variable_values=params)
        return result

    def save_payment_method(self, nonce: str = None) -> BraintreePaymentMethod:
        """
        Use nonce to save payment method to vault.

        Returns a BraintreePaymentMethod data object.
        """
        query = gql(
            """
            mutation VaultPaymentMethod($input: VaultPaymentMethodInput!) {
                vaultPaymentMethod(input: $input) {
                    paymentMethod {
                    id
                    usage
                    details {
                        __typename
                        ... on CreditCardDetails {
                        cardholderName
                        last4      
                        expirationMonth
                        expirationYear 
                        }
                        
                    }
                    }
                    verification {
                    status
                    }
                }
            }
            """
        )
        params = {
            "input": {
                "paymentMethodId": nonce,
                "customerId": 4
            }
        }
        result = self._client.execute(query, variable_values=params)

        return BraintreePaymentMethod(result)
