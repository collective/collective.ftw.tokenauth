from collective.ftw.tokenauth.testing import FTW_TOKENAUTH_FUNCTIONAL_TESTING
from collective.ftw.tokenauth.testing import FTW_TOKENAUTH_INTEGRATION_TESTING
from pytest_plone import fixtures_factory


pytest_plugins = ["pytest_plone"]


globals().update(
    fixtures_factory((
        (FTW_TOKENAUTH_FUNCTIONAL_TESTING, "functional"),
        (FTW_TOKENAUTH_INTEGRATION_TESTING, "integration"),
    ))
)
