import uuid
from typing import Dict
from django.conf import settings
from django.db import models

from .settings import braintree_settings


class Customer(models.Model):
    id = models.CharField(primary_key=True, max_length=24)
    owner = models.OneToOneField(
        braintree_settings.CUSTOMER_MODEL,
        on_delete=models.PROTECT,
        related_name="braintree_customer"
    )


class PaymentMethod(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    payement_method_id = models.CharField(max_length=255)
    last4 = models.CharField(max_length=4)
    exp_month = models.CharField(max_length=2)
    exp_year = models.CharField(max_length=2)

    def __unicode__(self):
        return self.id


class Transaction(models.Model):
    """
    Model containing records of payments received.

    item: Model
        The item being paid, eg. invoice, order, paycheck.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(
        braintree_settings.INVOICE_MODEL,
        on_delete=models.PROTECT,
        related_name='braintree_transactions'
    )
    response_code = models.CharField(max_length=4)
    total = models.DecimalField(
        max_digits=braintree_settings.MAX_CURRENCY_DIGITS, decimal_places=2)
    created = models.DateTimeField()
    transaction_id = models.CharField(max_length=128)

    def reverse(self):
        # TODO implement
        pass

    def __unicode__(self):
        return '%s charged $%s - %s' % (self.item, self.amount, self.transaction_id)


class AbstractBaseCustomerModel(models.Model):
    """
    Abstract implementation for the model that the Braintree Customer model will
    be setup to accept payments from. Company, Customer, User, etc.

    Fields listed here are passed to Braintree when creating a Braintree customer.

    Full list of other customer info that can be specified for a Braintree customer - 
    https://graphql.braintreepayments.com/reference/#input_object--customerinput

    Fields
    ----------
    company_name : str
        Name of the company making payments.
    first_name : str
        First name of the customer or company contact.
    last_name : str
        Last name of the customer or company contact.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_name = models.CharField(max_length=60, null=True, blank=True)
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        abstract = True


class AbstractBaseInvoiceModel(models.Model):
    """
    Abstract implementation for the model that the Braintree Customer model will
    be setup to accept payments from. Invoice, Membership, etc.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.OneToOneField(
        braintree_settings.CUSTOMER_MODEL,
        on_delete=models.PROTECT,
        related_name="braintree_customer"
    )

    @property
    def total(self):
        return self.subtotal + self.tax

    @property
    def subtotal(self):
        return 0

    def tax(self):
        return 0

    class Meta:
        abstract = True
