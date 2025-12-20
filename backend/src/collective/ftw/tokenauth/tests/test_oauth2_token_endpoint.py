# from ftw.builder import Builder
# from ftw.builder import create
from collective.ftw.tokenauth.oauth2.browser.oauth2_token import JWT_BEARER_GRANT_TYPE
from collective.ftw.tokenauth.tests import FunctionalTestCase
from collective.ftw.tokenauth.tests.utils import build_jwt_grant
from collective.ftw.tokenauth.tests.utils import build_key_pair
from plone import api
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME

import jwt
import requests
import transaction


class TestOAuth2TokenEndpoint(FunctionalTestCase):
    def setUp(self):
        super().setUp()
        self.keypair = self.plugin.issue_keypair(TEST_USER_ID, "My Service Key")
        # self.valid_assertion = create(Builder("jwt_grant").from_keypair(self.keypair))
        self.valid_assertion = build_jwt_grant(self.keypair)

        transaction.commit()
        self.token_url = self.portal.absolute_url() + "/@@oauth2-token"

    def test_only_accepts_post(self):
        response = requests.get(self.token_url, timeout=5)
        self.assertEqual(405, response.status_code)

        self.assertEqual(
            {"error": "invalid_request", "error_description": "POST only"},
            response.json(),
        )

    def test_sets_cache_headers(self):
        data = {"grant_type": JWT_BEARER_GRANT_TYPE, "assertion": self.valid_assertion}
        response = requests.post(self.token_url, data=data, timeout=5)
        self.assertIn("Pragma", response.headers)
        self.assertEqual("no-cache", response.headers["Pragma"])
        self.assertIn("Cache-Control", response.headers)
        self.assertEqual("no-store", response.headers["Cache-Control"])

    def test_sets_content_type_header(self):
        data = {"grant_type": JWT_BEARER_GRANT_TYPE, "assertion": self.valid_assertion}
        response = requests.post(self.token_url, data=data, timeout=5)
        self.assertIn("Content-Type", response.headers)
        self.assertEqual("application/json", response.headers["Content-Type"])

    def test_rejects_missing_grant_types(self):
        data = {"assertion": self.valid_assertion}
        response = requests.post(self.token_url, data=data, timeout=5)
        self.assertEqual(400, response.status_code)

        self.assertEqual(
            {"error": "invalid_request", "error_description": "Missing 'grant_type'"},
            response.json(),
        )

    def test_rejects_unknown_grant_types(self):
        data = {"grant_type": "unknown", "assertion": self.valid_assertion}
        response = requests.post(self.token_url, data=data, timeout=5)
        self.assertEqual(400, response.status_code)

        self.assertEqual(
            {
                "error": "invalid_request",
                "error_description": f"Only grant type '{JWT_BEARER_GRANT_TYPE}' is supported",  # noqa: E501
            },
            response.json(),
        )

    def test_rejects_missing_assertion(self):
        data = {"grant_type": JWT_BEARER_GRANT_TYPE}
        response = requests.post(self.token_url, data=data, timeout=5)
        self.assertEqual(400, response.status_code)

        self.assertEqual(
            {"error": "invalid_request", "error_description": "Missing 'assertion'"},
            response.json(),
        )

    def test_rejects_unsupported_signature_algorithm(self):
        # Create (empty) JWT with unsupported signature algorithm
        assertion = jwt.encode({}, "some-key", algorithm="HS256")

        data = {"grant_type": JWT_BEARER_GRANT_TYPE, "assertion": assertion}
        response = requests.post(self.token_url, data=data, timeout=5)
        self.assertEqual(400, response.status_code)

        self.assertEqual(
            {
                "error": "invalid_request",
                "error_description": "Only RS256 signature algorithm is supported",
            },
            response.json(),
        )

    def test_rejects_unknown_service_key(self):
        # not_stored_keypair = create(Builder("keypair"))
        not_stored_keypair = build_key_pair()
        # assertion = create(Builder("jwt_grant").from_keypair(not_stored_keypair))
        assertion = build_jwt_grant(not_stored_keypair)
        data = {"grant_type": JWT_BEARER_GRANT_TYPE, "assertion": assertion}
        response = requests.post(self.token_url, data=data, timeout=5)
        self.assertEqual(400, response.status_code)

        self.assertEqual(
            {"error": "invalid_grant", "error_description": "No associated key found"},
            response.json(),
        )

    def test_rejects_invalid_jwt_assertion(self):
        # In-depth tests for JWT grant validation are tested in
        # collective.ftw.tokenauth.tests.test_jwt_grant_validation.py
        # invalid_assertion = create(
        #     Builder("jwt_grant")
        #     .having(aud="http://bogus.example.org")
        #     .from_keypair(self.keypair)
        # )
        invalid_assertion = build_jwt_grant(
            self.keypair, {"aud": "http://bogus.example.org"}
        )

        data = {"grant_type": JWT_BEARER_GRANT_TYPE, "assertion": invalid_assertion}
        response = requests.post(self.token_url, data=data, timeout=5)
        self.assertEqual(400, response.status_code)

        self.assertEqual(
            {"error": "invalid_grant", "error_description": "Audience doesn't match"},
            response.json(),
        )

    def test_issues_access_token_for_valid_grant(self):
        data = {"grant_type": JWT_BEARER_GRANT_TYPE, "assertion": self.valid_assertion}
        response = requests.post(self.token_url, data=data, timeout=5)
        transaction.commit()

        self.assertEqual(200, response.status_code)
        response_json = response.json()

        self.assertCountEqual(
            ["access_token", "token_type", "expires_in"], list(response_json.keys())
        )
        self.assertEqual("Bearer", response_json["token_type"])
        self.assertEqual(3600, response_json["expires_in"])

        # Make sure the token we got is valid and can be used to authenticate
        token = response_json["access_token"]
        creds = {"access_token": token, "extractor": self.plugin.getId()}
        self.assertEqual(
            (TEST_USER_ID, TEST_USER_NAME),
            self.plugin.authenticateCredentials(creds),
        )

    def test_respects_custom_access_token_lifetime(self):
        self.plugin.access_token_lifetime = 7200
        transaction.commit()

        data = {"grant_type": JWT_BEARER_GRANT_TYPE, "assertion": self.valid_assertion}
        response = requests.post(self.token_url, data=data, timeout=5)
        self.assertEqual(200, response.status_code)
        self.assertEqual(7200, response.json()["expires_in"])

    def test_issues_impersonated_access_token(self):
        self.portal.manage_permission(
            "collective.ftw.tokenauth: Impersonate user", ["Member"], acquire=False
        )
        api.user.create(email="jane@plone.org", username="jane")
        # assertion = create(
        #     Builder("jwt_grant").from_keypair(self.keypair).for_subject("jane")
        # )
        assertion = build_jwt_grant(self.keypair, {"sub": "jane"})
        transaction.commit()

        data = {"grant_type": JWT_BEARER_GRANT_TYPE, "assertion": assertion}
        response = requests.post(self.token_url, data=data, timeout=5)
        transaction.commit()

        self.assertEqual(200, response.status_code)
        response_json = response.json()
        self.assertCountEqual(
            ["access_token", "token_type", "expires_in"], list(response_json.keys())
        )
        self.assertEqual("Bearer", response_json["token_type"])
        self.assertEqual(3600, response_json["expires_in"])

        # Make sure the token we got is valid and can be used to authenticate
        token = response_json["access_token"]
        creds = {"access_token": token, "extractor": self.plugin.getId()}
        self.assertEqual(("jane", "jane"), self.plugin.authenticateCredentials(creds))

    def test_rejects_impersonated_access_token_without_permission(self):
        api.user.create(email="jane@plone.org", username="jane")
        # assertion = create(
        #     Builder("jwt_grant").from_keypair(self.keypair).for_subject("jane")
        # )
        assertion = build_jwt_grant(self.keypair, {"sub": "jane"})
        transaction.commit()

        data = {"grant_type": JWT_BEARER_GRANT_TYPE, "assertion": assertion}
        response = requests.post(self.token_url, data=data, timeout=5)
        self.assertEqual(400, response.status_code)

        self.assertEqual(
            {
                "error": "invalid_grant",
                "error_description": "JWT subject doesn't match user_id of service key.",  # noqa: E501
            },
            response.json(),
        )

    def test_rejects_impersonated_access_token_without_service_user(self):
        keypair = self.plugin.issue_keypair(SITE_OWNER_NAME, "A Service Key")
        # assertion = create(
        #     Builder("jwt_grant").from_keypair(keypair).for_subject("jane")
        # )
        assertion = build_jwt_grant(keypair, {"sub": "jane"})
        transaction.commit()

        data = {"grant_type": JWT_BEARER_GRANT_TYPE, "assertion": assertion}
        response = requests.post(self.token_url, data=data, timeout=5)
        self.assertEqual(400, response.status_code)

        self.assertEqual(
            {
                "error": "invalid_grant",
                "error_description": "Service key user not found.",
            },
            response.json(),
        )
