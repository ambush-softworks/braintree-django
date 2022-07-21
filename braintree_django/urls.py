from django.urls import path

from .views import PaymentMethodView


app_name = "braintree_django"


urlpatterns = [
    path('braintree/payment/method/<uuid:customer>',
         PaymentMethodView.as_view(),
         name="payment-method"),
    path('braintree/payment/pay/<uuid:item>',
         PayView.as_view(),
         name="pay-item")
]
