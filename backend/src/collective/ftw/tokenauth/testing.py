from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.testing.zope import WSGI_SERVER_FIXTURE
from plone import api
import os, time
from plone.testing.layer import Layer

import collective.ftw.tokenauth


DEFAULT_TESTING_TOKEN_URI = "http://nohost/plone/@@oauth2-token"  # noqa: S105

ENV_VARS = {"LC_ALL": "en_US.UTF-8", "LANG": "en_US.UTF-8", "TZ": "UTC"}


class LocaleFixture(Layer):
    """We need to create a testing layer to set the en_US.UTF-8 locale
    this way the output of datetime objects is consistent both locally
    and on GHA.

    To get the tests running correctly you may need to install the said
    locale in your device.
    """

    def setUp(self):
        self._orig_content = {}
        for key, value in ENV_VARS.items():
            if key in os.environ:
                self._orig_content[key] = value

        os.environ["LC_ALL"] = "en_US.UTF-8"
        os.environ["LANG"] = "en_US.UTF-8"
        os.environ["TZ"] = "UTC"

    def tearDown(self):
        # Restore the original values
        for key in ENV_VARS:
            del os.environ[key]

        for key, value in self._orig_content.items():
            os.environ[key] = value


LOCALE_FIXTURE = LocaleFixture()


class FtwTokenAuthLayer(PloneSandboxLayer):
    defaultBases = (
        LOCALE_FIXTURE,
        PLONE_APP_CONTENTTYPES_FIXTURE,
    )

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import plone.restapi

        self.loadZCML(package=plone.restapi)
        self.loadZCML(package=collective.ftw.tokenauth)

    def setUpPloneSite(self, portal):
        applyProfile(portal, "collective.ftw.tokenauth:default")
        uf = portal.acl_users
        self["plugin"] = uf["token_auth"]

        language_tool = api.portal.get_tool("portal_languages")
        language_tool.addSupportedLanguage("en")

        applyProfile(portal, "plone.restapi:default")


FTW_TOKENAUTH_FIXTURE = FtwTokenAuthLayer()

FTW_TOKENAUTH_INTEGRATION_TESTING = IntegrationTesting(
    bases=(FTW_TOKENAUTH_FIXTURE,), name="FtwtokenauthLayer:IntegrationTesting"
)

FTW_TOKENAUTH_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(
        FTW_TOKENAUTH_FIXTURE,
        WSGI_SERVER_FIXTURE,
    ),
    name="FtwtokenauthLayer:FunctionalTestingr",
)
