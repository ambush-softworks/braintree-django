import json
from base64 import b64encode
from typing import Dict
from django.conf import settings

from gql import gql, Client
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


class BraintreeCustomer:
    def __init__(self, id: str = None, company_name: str = None, first_name: str = None, last_name: str = None, gql: BraintreeGraphQL = None):
        self.gql = gql
        self.id = id
        self.company_name = company_name
        self.first_name = first_name
        self.last_name = last_name

        self.connect()

    def connect(self):
        if self.gql == None:
            self.gql = BraintreeGraphQL()

    def to_dict(self) -> Dict:
        """
        Returns dict containing any fields that contain values.

        Used to provid parameters for CreateCustomer mutation.
        """
        data = {}
        if self.id:
            data.update(
                {"id": self.id}
            )
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
        return data

    def create(self):
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
                "customer": self.to_dict()
            }
        }

        result = self.gql._client.execute(query, variable_values=params)
        self.id = result['createCustomer']['customer']['id']
        return self.id


class BraintreePaymentMethod:
    # payment_method: Dict
    # verification: Dict

    def __init__(
        self,
        customer_id: str,
        method_id: str = None,
        cardholder_name: str = None,
        last_four: str = None,
        exp_month: str = None,
        exp_year: str = None,
        gql: BraintreeGraphQL = None
    ):
        # self.payment_method = data.vaultPaymentMethod.payment_method
        # self.verification = data.vaultPaymentMethod.verification
        self.gql = gql
        self.customer_id = customer_id
        self.method_id = method_id
        self.cardholder_name = cardholder_name
        self.last_four = last_four
        self.exp_month = exp_month
        self.exp_year = exp_year

        self.connect()

    def connect(self):
        if self.gql == None:
            self.gql = BraintreeGraphQL()

    def vault_payment_method(self, nonce: str = None):
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
                "customerId": self.customer_id
            }
        }
        result = self.gql._client.execute(query, variable_values=params)

        payment_method = result['vaultPaymentMethod']['paymentMethod']

        self.method_id = payment_method['id']
        self.cardholder_name = payment_method['details']['cardholderName']
        self.last_four = payment_method['details']['last4']
        self.exp_month = payment_method['details']['expirationMonth']
        self.exp_year = payment_method['details']['expirationYear']

        return result

    def get_client_token(self):
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
                    "customerId": self.customer_id
                }
            }
        }

        result = self.gql._client.execute(query, variable_values=params)

        self.client_token = result['createClientToken']['clientToken']

        return self.client_token

    def id(self) -> str:
        return self.payment_method.id
