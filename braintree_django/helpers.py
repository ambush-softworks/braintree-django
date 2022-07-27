import json
import logging
from typing import Dict

from django.contrib.contenttypes.models import ContentType

from gql import gql
from .graphql import BraintreeGraphQL
from .settings import braintree_settings

logger = logging.getLogger(__name__)


class BraintreeCustomer:
    """
    Helper class for interfacing django models and the Braintree API.

    Fields
    ----------
    gql : BraintreeGraphQL
        A helper class for handing the Braintree GraphQL connection and client.

    id : str
        id of the object specified as the model specifed by the BRAINTREE_CUSTOMER_MODEL
        setting. The model to be tied to the Braintree customer in the API.
    """

    def __init__(self, id: str):
        self.gql = BraintreeGraphQL()
        self.id = id
        self.fetch_data(self.id)

    # def connect(self):
    #     if self.gql == None:
    #         self.gql = BraintreeGraphQL()

    def to_dict(self) -> Dict:
        """
        Converts set class fields into a dict as params for gql mutations.

            Returns:
                Dict of customer data
        """
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
        return data

    def fetch_data(self, customer_id: str):
        """
        Gets customer model ContentType and gets customer data in order to create a customer
        with Braintree.

        Uses ContentType to get the model class that's specifed by BRAINTREE_CUSTOMER_MODEL 
        setting.
        """
        model_name = braintree_settings.CUSTOMER_MODEL.split('.', 1)

        try:
            customer_model_type = ContentType.objects.get(
                app_label__iexact=model_name[0],
                model__iexact=model_name[1]
            )
        except Exception as e:
            message = "Failed to find CUSTOMER_MODEL.: {}".format(e)
            logger.error(message)
            print(message)

        customer_obj = customer_model_type.get_object_for_this_type(
            id=customer_id)

        self.company_name = customer_obj.company_name
        self.first_name = customer_obj.contact_first_name
        self.last_name = customer_obj.contact_last_name

    def create(self) -> str:
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
            result = self.gql.client.execute(query, variable_values=params)
            self.id = result['createCustomer']['customer']['id']
            return self.id
        except Exception as e:
            message = "Failed to create Braintree customer: {}".format(e)
            logger.error(message)
            print(message)

    def update(self, vault_id: str) -> Dict:
        """
        Updates customer data to Braintree API.

            Returns:
                API json result, or None, if no id is set.

            Parameters:
                vault_id (str)
                    The vault_id from the CustomerVault that ties to the Braintree customerId
        """
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
                    "customerId": vault_id,
                    "customer": self.to_dict()
                }
            }

            result = self.gql.client.execute(query, variable_values=params)
        else:
            logger.error("No vault_id provided to BraintreeCustomer update.")
            return None


class BraintreePaymentMethod:
    """
    Helper class to interface django with the Braintree API

    Fields
    ----------
    customer_id: str
        customerId in the Braintree API and customer_id of the CustomerVault django model.

    method_id: str
        The id of the payment method in the Braintree API.

    exp_month: str
        Two digit month.

    exp_year: str
        Four digit year.
    """

    def __init__(
        self,
        customer_id: str,
        method_id: str = None,
        cardholder_name: str = None,
        last_four: str = None,
        exp_month: str = None,
        exp_year: str = None,
    ):
        self.gql = BraintreeGraphQL()
        self.customer_id = customer_id
        self.method_id = method_id
        self.cardholder_name = cardholder_name
        self.last_four = last_four
        self.exp_month = exp_month
        self.exp_year = exp_year

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
        result = self.gql.client.execute(query, variable_values=params)

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

        print(params)

        try:
            result = self.gql.client.execute(query, variable_values=params)
            self.client_token = result['createClientToken']['clientToken']
            return self.client_token
        except Exception as e:
            message = "Failed to setup gql client: {}".format(e)
            logger.error(message)
            print(message)

    def id(self) -> str:
        return self.payment_method.id
