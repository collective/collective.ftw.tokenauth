from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.testing.zope import WSGI_SERVER_FIXTURE

import collective.ftw.tokenauth


DEFAULT_TESTING_TOKEN_URI = "http://nohost/plone/@@oauth2-token"  # noqa: S105


class FtwTokenAuthLayer(PloneSandboxLayer):
    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import plone.restapi

        self.loadZCML(package=plone.restapi)
        self.loadZCML(package=collective.ftw.tokenauth)

    def setUpPloneSite(self, portal):
        applyProfile(portal, "collective.ftw.tokenauth:default")
        uf = portal.acl_users
        self["plugin"] = uf["token_auth"]

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
