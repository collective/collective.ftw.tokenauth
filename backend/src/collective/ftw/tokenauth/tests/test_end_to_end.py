from bs4 import BeautifulSoup
from collective.ftw.tokenauth.tests import FunctionalZServerTestCase
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from zope.testbrowser.browser import Browser

import json
import jwt
import requests
import time


GRANT_TYPE = "urn:ietf:params:oauth:grant-type:jwt-bearer"


class TestEndToEndAuthenticationFlow(FunctionalZServerTestCase):
    def test_end_to_end_happy_path(self):
        browser = Browser()
        browser.handleErrors = False

        # Step 1 - Issue service key and save it
        browser.open(self.portal.absolute_url() + "/login")
        browser.getControl(name="__ac_name").value = TEST_USER_NAME
        browser.getControl(name="__ac_password").value = TEST_USER_PASSWORD
        browser.getControl(name="buttons.login").click()

        browser.open(self.portal.absolute_url() + "/@@manage-service-keys")
        browser.getLink("Issue new service key").click()
        browser.getControl("Title").value = "My new key"
        # No IP range restriction, we test this separately
        browser.getControl("Issue key").click()

        self.assertIn("Download Service Key", browser.contents)

        soup = BeautifulSoup(browser.contents, "html.parser")
        # get the contents of the item with css class .json-keyfile
        keyfile_data = json.loads(soup.css.select_one(".json-keyfile").text)

        private_key = keyfile_data["private_key"]
        token_uri = keyfile_data["token_uri"]

        browser.open(self.portal.absolute_url() + "/logout")
        self.assertIn("You are now logged out", browser.contents)

        # Step 2 - Create a JWT grant and sign it with private key
        claim_set = {
            "aud": token_uri,
            "iss": keyfile_data["client_id"],
            "sub": keyfile_data["user_id"],
            "iat": int(time.time()),
            "exp": int(time.time() + (60 * 59)),
        }
        grant_token = jwt.encode(claim_set, private_key, algorithm="RS256")

        # Step 3 - Exchange the JWT grant for an access token by making
        # a token request to the OAuth2 token endpoint
        payload = {"grant_type": GRANT_TYPE, "assertion": grant_token}
        token_response = requests.post(token_uri, data=payload)
        token = token_response.json()["access_token"]

        # Step 4 - Use the access token to make authenticated requests
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(self.portal.absolute_url(), headers=headers)
        self.assertIn(TEST_USER_ID, response.text)

        # Test with plone.restapi as well
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

        response = requests.get(self.portal.absolute_url(), headers=headers)
        self.assertIn("title", response.json())
        self.assertEqual(response.json()["title"], "Plone site")
