import json
import logging
from typing import Dict

from django.contrib.contenttypes.models import ContentType

from gql import gql
from .graphql import BraintreeGraphQL
from .settings import braintree_settings

logger = logging.getLogger(__name__)


class BraintreeCustomer:
    def __init__(self, id: str = None, company_name: str = None, first_name: str = None, last_name: str = None, gql: BraintreeGraphQL = None):
        self.gql = gql
        self.id = id
        # self.company_name = company_name
        # self.first_name = first_name
        # self.last_name = last_name

        self.fetch_data(self.id)

        self.connect()

    def connect(self):
        if self.gql == None:
            self.gql = BraintreeGraphQL()

    # def model_type(self):

    def to_dict(self) -> Dict:
        """
        Returns dict containing any fields that contain values.

        Used to provid parameters for customer mutations.
        """
        data = {}
        # if self.id:
        #     data.update(
        #         {"id": str(self.id)}
        #     )
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

    def fetch_data(self, customer_id):
        """
        Gets customer model ContentType and gets customer data in order to create a customer with Braintree.
        """
        model_name = braintree_settings.CUSTOMER_MODEL.split('.', 1)

        print("Customer Model Name: {}".format(model_name[1]))
        print("Customer Model App Label: {}".format(model_name[0]))

        try:
            customer_model_type = ContentType.objects.get(
                app_label__iexact=model_name[0],
                model__iexact=model_name[1]
            )
            print("Content Type: {}".format(customer_model_type))
        except Exception as e:
            print(e)

        customer_obj = customer_model_type.get_object_for_this_type(
            id=customer_id)
        print("Customer Object: {}".format(customer_obj))

        self.company_name = customer_obj.company_name
        self.first_name = customer_obj.contact_first_name
        self.last_name = customer_obj.contact_last_name

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

        try:
            result = self.gql._client.execute(query, variable_values=params)
            print("Customer Result: {}".format(result))
            self.id = result['createCustomer']['customer']['id']
        except Exception as e:
            logger.error("Failed to create Braintree customer: {}".format(e))
            return None
        return self.id

    def update(self):
        if self.id is not None:
            query = gql(
                """
                mutation UpdateCustomer($input: CustomerInput!) {
                    updateCustomer(input: $input) {
                        customer {
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
                    "customerId": self.id(),
                    "customer": self.to_dict()
                }
            }

            result = self.gql._client.execute(query, variable_values=params)
            print("updateCustomer Result: {}".format(result))
        else:
            print("No customerID to update.")


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
