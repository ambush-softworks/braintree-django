"""
Settings for braintree_django are all set in BRAINTREE setting.

BRAINTREE_CUSTOMER_MODEL = "jobs.Company"
BRAINTREE_INVOICE_MODEL = "invoices.Invoice"
BRAINTREE = {
    "BRAINTREE_MERCHANT_ID": "<merchant id>",
    "BRAINTREE_PUBLIC_KEY": "<public key>",
    "BRAINTREE_PRIVATE_KEY": "<private key>",
    "MAX_CURRENCY_DIGITS": 3,
}

"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test.signals import setting_changed
from django.utils.module_loading import import_string


USER_SETTINGS = getattr(settings, "BRAINTREE", None)

CUSTOMER_MODEL = getattr(
    settings, "BRAINTREE_CUSTOMER_MODEL", settings.AUTH_USER_MODEL)
INVOICE_MODEL = getattr(
    settings, "BRAINTREE_INVOICE_MODEL", settings.AUTH_USER_MODEL)


# default settings
DEFAULTS = {
    "BRAINTREE_MERCHANT_ID": "",
    "BRAINTREE_PUBLIC_KEY": "",
    "BRAINTREE_PRIVATE_KEY": "",
    "MAX_CURRENCY_DIGITS": 7,
    "CUSTOMER_MODEL": CUSTOMER_MODEL,
    "INVOICE_MODEL": INVOICE_MODEL,
    "BRAINTREE_SANDBOX_URL": "https://payments.sandbox.braintree-api.com/graphql",
    "BRAINTREE_PRODUCTION_URL": "https://payments.braintree-api.com/graphql",
}

MANDATORY = (
    "BRAINTREE_MERCHANT_ID",
    "BRAINTREE_PUBLIC_KEY",
    "BRAINTREE_PRIVATE_KEY",
)

IMPORT_STRINGS = ()


def perform_import(val, setting_name):
    """
    If the given setting is a string import notation,
    then perform the necessary import or imports.
    """
    if val is None:
        return None
    elif isinstance(val, str):
        return import_from_string(val, setting_name)
    elif isinstance(val, (list, tuple)):
        return [import_from_string(item, setting_name) for item in val]
    return val


def import_from_string(val, setting_name):
    """
    Attempt to import a class from a string representation.
    """
    try:
        return import_string(val)
    except ImportError as e:
        msg = "Could not import %r for setting %r. %s: %s." % (
            val, setting_name, e.__class__.__name__, e)
        raise ImportError(msg)


class BraintreeSettings:
    def __init__(self, user_settings=None, defaults=None, import_strings=None, mandatory=None):
        self._user_settings = user_settings or {}
        self.defaults = defaults or DEFAULTS
        self.import_strings = import_strings or IMPORT_STRINGS
        self.mandatory = mandatory or ()
        self._cached_attrs = set()

    @property
    def user_settings(self):
        if not hasattr(self, "_user_settings"):
            self._user_settings = getattr(settings, "BRAINTREE", {})
        return self._user_settings

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError("Invalid Braintree setting: %s" % attr)
        try:
            # Check if present in user settings
            val = self.user_settings[attr]
        except KeyError:
            # Fall back to defaults
            val = self.defaults[attr]

        # Coerce import strings into classes
        if val and attr in self.import_strings:
            val = perform_import(val, attr)

        self.validate_setting(attr, val)

        # Cache the result
        self._cached_attrs.add(attr)
        setattr(self, attr, val)
        return val

    def validate_setting(self, attr, val):
        if not val and attr in self.mandatory:
            raise AttributeError(
                "Braintree setting: %s is mandatory" % attr)

    def reload(self):
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()
        if hasattr(self, "_user_settings"):
            delattr(self, "_user_settings")


braintree_settings = BraintreeSettings(
    USER_SETTINGS, DEFAULTS, IMPORT_STRINGS, MANDATORY)


def reload_braintree_settings(*args, **kwargs):
    setting = kwargs["setting"]
    if setting == "BRAINTREE":
        braintree_settings.reload()


setting_changed.connect(reload_braintree_settings)
