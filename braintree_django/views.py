from django.http import HttpResponse
from django.shortcuts import render
from django.views import View

from .graphql import BraintreeGraphQL

from .models import PaymentMethod


class PaymentMethodView(View):
    template_name = 'braintree_django/payment_method.html'

    def get(self, request, *args, **kwargs):
        print(">>> GET >>>")
        braintree = BraintreeGraphQL()

        client_token = braintree.client_token()

        print("Braintree client token: %s" % client_token)

        # TODO make url to pass vault_relation object
        context = {
            'braintree_client_token': client_token,
            'vault_relation': vault_relation
        }

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        print(">>> POST >>>\n")
        braintree = BraintreeGraphQL()
        nonce = request.POST['paymentMethodNonce']

        print("Payment nonse: %s" % (nonce))
        print('\n')

        payment_method = braintree.save_payment_method(nonce=nonce)

        # api.create_customer(company_name="Test Company")
        # result = api.process_sale(nonce=request.POST['paymentMethodNonce'])
        # print(result)
        # print('\n')
        # print(result.transaction)
        return HttpResponse('Ok')
