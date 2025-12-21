from bs4 import BeautifulSoup
from collective.ftw.tokenauth.pas.storage import CredentialStorage
from collective.ftw.tokenauth.permissions import ManageOwnServiceKeys
from collective.ftw.tokenauth.testing import FTW_TOKENAUTH_FUNCTIONAL_TESTING
from collective.ftw.tokenauth.tests import FunctionalTestCase
from collective.ftw.tokenauth.tests.utils import build_access_token
from collective.ftw.tokenauth.tests.utils import build_service_key
from datetime import datetime
from freezegun import freeze_time
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.testing.zope import Browser

import json
import re
import transaction


class TestManageServiceKeysView(FunctionalTestCase):
    layer = FTW_TOKENAUTH_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.portal_url = self.portal.absolute_url()
        self.browser = Browser(self.app)
        self.plugin = self.portal.acl_users["token_auth"]

        transaction.commit()

    def _login(self):
        self.browser.open(f"{self.portal_url}/login")
        self.browser.getControl(name="__ac_name").value = TEST_USER_NAME
        self.browser.getControl(name="__ac_password").value = TEST_USER_PASSWORD
        self.browser.getControl(name="buttons.login").click()

    def test_manage_key_views_require_permission(self):
        # Unmap the 'ftw.tokenauth: Manage own Service Keys'
        # permission from any roles
        self.portal.manage_permission(ManageOwnServiceKeys, roles=[])
        transaction.commit()

        self._login()

        self.browser.open(f"{self.portal_url}/@@manage-service-keys")
        self.assertIn("Insufficient Privileges", self.browser.contents)

        self.browser.open(f"{self.portal_url}/@@manage-service-keys-issue")
        self.assertIn("Insufficient Privileges", self.browser.contents)

        self.browser.open(f"{self.portal_url}/@@manage-service-keys-edit")
        self.assertIn("Insufficient Privileges", self.browser.contents)

        self.browser.open(f"{self.portal_url}/@@manage-service-keys-logs")
        self.assertIn("Insufficient Privileges", self.browser.contents)

    def test_issuing_key_via_manage_service_keys_view(self):
        self._login()
        self.browser.open(f"{self.portal_url}/@@manage-service-keys")

        self.browser.getLink("Issue new service key").click()
        with freeze_time(datetime(2018, 1, 1, 15, 30)):
            self.browser.getControl(name="form.widgets.title").value = "My new key"
            self.browser.getControl(name="form.widgets.ip_range").value = (
                "192.168.0.0/16"
            )
            self.browser.getControl(name="form.buttons.save").click()

        soup = BeautifulSoup(self.browser.contents, "html.parser")
        status_message = soup.css.select(".statusmessage-info")

        match = re.search("Key created: (.*)", str(status_message))
        self.assertTrue(match)
        displayed_key_id = match.group(1)

        storage = CredentialStorage(self.plugin)
        self.assertEqual(1, len(storage.list_service_keys(TEST_USER_ID)))
        service_key = storage.list_service_keys(TEST_USER_ID)[0]

        self.assertEqual(displayed_key_id, service_key["key_id"])
        self.assertEqual("My new key", service_key["title"])
        self.assertEqual(datetime(2018, 1, 1, 15, 30), service_key["issued"])
        self.assertEqual(TEST_USER_ID, service_key["user_id"])
        self.assertIn("client_id", service_key)
        self.assertEqual("192.168.0.0/16", service_key["ip_range"])
        self.assertIn("public_key", service_key)

    def test_issuing_key_displays_private_key_for_download(self):
        self._login()
        self.browser.open(f"{self.portal_url}/@@manage-service-keys")
        self.browser.getLink("Issue new service key").click()

        self.browser.getControl(name="form.widgets.title").value = "My new key"
        self.browser.getControl(name="form.widgets.ip_range").value = "192.168.0.0/16"
        self.browser.getControl(name="form.buttons.save").click()

        soup = BeautifulSoup(self.browser.contents, "html.parser")
        status_message = soup.css.select(".statusmessage-info")

        match = re.search("Key created: (.*)", str(status_message))
        self.assertTrue(match)

        storage = CredentialStorage(self.plugin)
        self.assertEqual(1, len(storage.list_service_keys(TEST_USER_ID)))
        key = storage.list_service_keys(TEST_USER_ID)[0]

        self.assertIn("Download your service key.", self.browser.contents)
        self.assertIn("My new key", self.browser.contents)

        json_keyfile = soup.css.select(".json-keyfile")[0]
        keyfile_data = json.loads(json_keyfile.text)
        self.assertCountEqual(
            ["key_id", "client_id", "issued", "user_id", "token_uri", "private_key"],
            keyfile_data.keys(),
        )

        # TODO: Assert on private key contents, if possible
        self.assertEqual(key["key_id"], keyfile_data["key_id"])
        self.assertEqual(key["issued"].isoformat(), keyfile_data["issued"])
        self.assertEqual(TEST_USER_ID, keyfile_data["user_id"])
        self.assertEqual(f"{self.portal_url}/@@oauth2-token", keyfile_data["token_uri"])

    def test_issuing_key_without_ip_range_is_allowed(self):
        self._login()

        self.browser.open(f"{self.portal_url}/@@manage-service-keys")
        self.browser.getLink("Issue new service key").click()

        self.browser.getControl(name="form.widgets.title").value = (
            "Key without IP range"
        )
        self.browser.getControl(name="form.buttons.save").click()

        storage = CredentialStorage(self.plugin)
        self.assertEqual(1, len(storage.list_service_keys(TEST_USER_ID)))
        key = storage.list_service_keys(TEST_USER_ID)[0]

        self.assertEqual("Key without IP range", key["title"])
        self.assertEqual(None, key["ip_range"])

    def test_issuing_key_without_title_is_not_allowed(self):
        self._login()
        self.browser.open(f"{self.portal_url}/@@manage-service-keys")
        self.browser.getLink("Issue new service key").click()

        self.browser.getControl(name="form.buttons.save").click()

        self.assertIn("There were some errors.", self.browser.contents)
        self.assertIn("Required input is missing.", self.browser.contents)

        storage = CredentialStorage(self.plugin)
        self.assertEqual(0, len(storage.list_service_keys(TEST_USER_ID)))

    def test_issuing_key_with_invalid_ip_range_is_rejected(self):
        self._login()
        self.browser.open(f"{self.portal_url}/@@manage-service-keys")
        self.browser.getLink("Issue new service key").click()

        self.browser.getControl(name="form.widgets.title").value = (
            "Key with invalid IP range"
        )
        self.browser.getControl(name="form.widgets.ip_range").value = "192.168.5.5/16"
        self.browser.getControl(name="form.buttons.save").click()

        self.assertIn("There were some errors.", self.browser.contents)

        self.assertIn(
            "Allowed IP range specification in",
            self.browser.contents,
        )

        self.assertIn(
            "CIDR notation",
            self.browser.contents,
        )

        self.assertIn(
            "Multiple comma-separated addresses / networks may be supplied.",
            self.browser.contents,
        )
        self.assertIn(
            "Invalid IP range: 192.168.5.5/16 has host bits set", self.browser.contents
        )

        storage = CredentialStorage(self.plugin)
        self.assertEqual(0, len(storage.list_service_keys(TEST_USER_ID)))

    def test_issue_key_form_handles_cancelling(self):
        self._login()
        self.browser.open(f"{self.portal_url}/@@manage-service-keys")
        self.browser.getLink("Issue new service key").click()

        self.browser.getControl(name="form.buttons.cancel").click()

        self.assertIn("Key creation cancelled.", self.browser.contents)

    def test_lists_issued_keys(self):
        with freeze_time(datetime(2017, 1, 1, 15, 30)):
            build_service_key(self.plugin, arguments={"title": "Key 1"})

        with freeze_time(datetime(2018, 5, 5, 12, 45)):
            build_service_key(
                self.plugin, arguments={"title": "Key 2", "ip_range": "192.168.0.0/16"}
            )
        transaction.commit()

        storage = CredentialStorage(self.plugin)
        keys = storage.list_service_keys(TEST_USER_ID)
        client_ids = [k["client_id"] for k in keys]

        self._login()
        self.browser.open(f"{self.portal_url}/@@manage-service-keys")
        soup = BeautifulSoup(self.browser.contents, "html.parser")
        table = soup.css.select("#table-service-keys")
        headings = table[0].css.select("thead tr th")
        heading_texts = [h.text for h in headings]
        self.assertCountEqual(
            ["", "Title", "Client-ID", "IP Range", "Issued", "Last Used", ""],
            heading_texts,
        )

        rows = table[0].css.select("tbody tr")
        first_row_texts = [r.text.strip() for r in rows[0].css.select("td")]
        second_row_texts = [r.text.strip() for r in rows[1].css.select("td")]

        self.assertCountEqual(
            [
                "",
                "Key 1",
                client_ids[0],
                "",
                "Jan 01, 2017 03:30 PM",
                "",
                "Edit",
            ],
            first_row_texts,
        )
        self.assertCountEqual(
            [
                "",
                "Key 2",
                client_ids[1],
                "192.168.0.0/16",
                "May 05, 2018 12:45 PM",
                "",
                "Edit",
            ],
            second_row_texts,
        )

    def test_revoking_key_via_manage_service_keys_view(self):
        service_key = build_service_key(self.plugin, arguments={"title": "My key"})
        transaction.commit()

        storage = CredentialStorage(self.plugin)
        users_keys = storage.list_service_keys(TEST_USER_ID)
        self.assertEqual(1, len(users_keys))
        stored_service_key = users_keys[0]

        # Guard assertion - make sure the issued key is actually in storage
        self.assertEqual(service_key["key_id"], stored_service_key["key_id"])
        self.assertEqual(service_key["public_key"], stored_service_key["public_key"])

        # Revoke the key
        self._login()
        self.browser.open(f"{self.portal_url}/@@manage-service-keys")

        self.browser.getControl("My key").click()
        self.browser.getControl("Revoke selected keys").click()

        # Got removed from storage
        self.assertEqual([], storage.list_service_keys(TEST_USER_ID))


class TestEditServiceKeysView(FunctionalTestCase):
    layer = FTW_TOKENAUTH_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.portal_url = self.portal.absolute_url()
        self.browser = Browser(self.app)
        self.plugin = self.portal.acl_users["token_auth"]

        transaction.commit()

    def _login(self):
        self.browser.open(f"{self.portal_url}/login")
        self.browser.getControl(name="__ac_name").value = TEST_USER_NAME
        self.browser.getControl(name="__ac_password").value = TEST_USER_PASSWORD
        self.browser.getControl(name="buttons.login").click()

    def test_editing_key_metadata(self):
        build_service_key(self.plugin)
        transaction.commit()

        self._login()
        self.browser.open(f"{self.portal_url}/@@manage-service-keys")
        self.browser.getLink("Edit").click()

        self.browser.getControl(name="form.widgets.title").value = "New title"
        self.browser.getControl(name="form.widgets.ip_range").value = "10.0.0.0/24"
        self.browser.getControl(name="form.buttons.save").click()

        self.assertIn("Data successfully updated.", self.browser.contents)

        storage = CredentialStorage(self.plugin)
        users_keys = storage.list_service_keys(TEST_USER_ID)
        self.assertEqual(1, len(users_keys))
        key = users_keys[0]

        self.assertEqual("New title", key["title"])
        self.assertEqual("10.0.0.0/24", key["ip_range"])

    def test_edit_key_form_validates_constraints(self):
        build_service_key(
            self.plugin, arguments={"title": "Some key", "ip_range": "192.168.0.0/16"}
        )
        transaction.commit()
        self._login()
        self.browser.open(f"{self.portal_url}/@@manage-service-keys")
        self.browser.getLink("Edit").click()

        self.browser.getControl(name="form.widgets.title").value = ""
        self.browser.getControl(name="form.widgets.ip_range").value = "10.0.5.5/24"
        self.browser.getControl(name="form.buttons.save").click()

        self.assertIn("There were some errors.", self.browser.contents)
        self.assertIn("Required input is missing.", self.browser.contents)
        self.assertIn("Allowed IP range specification in", self.browser.contents)
        self.assertIn("CIDR notation", self.browser.contents)
        self.assertIn(
            "Multiple comma-separated addresses / networks may be supplied.",
            self.browser.contents,
        )
        self.assertIn(
            "Invalid IP range: 10.0.5.5/24 has host bits set", self.browser.contents
        )

        storage = CredentialStorage(self.plugin)
        users_keys = storage.list_service_keys(TEST_USER_ID)
        self.assertEqual(1, len(users_keys))
        service_key = users_keys[0]

        # Key shouldn't have been updated
        self.assertEqual("Some key", service_key["title"])
        self.assertEqual("192.168.0.0/16", service_key["ip_range"])

    def test_edit_key_form_retains_widget_values_on_error(self):
        with freeze_time(datetime(2018, 1, 7, 15, 30)):
            service_key = build_service_key(
                self.plugin,
                arguments={
                    "title": "Some key",
                    "ip_range": "192.168.0.0/16",
                },
            )
        transaction.commit()

        self._login()
        self.browser.open(f"{self.portal_url}/@@manage-service-keys")
        self.browser.getLink("Edit").click()

        self.browser.getControl(name="form.widgets.title").value = ""
        self.browser.getControl(name="form.widgets.ip_range").value = "10.0.5.5/24"
        self.browser.getControl(name="form.buttons.save").click()

        self.assertIn("There were some errors.", self.browser.contents)

        self.assertIn("Required input is missing.", self.browser.contents)
        self.assertIn("Allowed IP range specification in", self.browser.contents)
        self.assertIn("CIDR notation", self.browser.contents)
        self.assertIn(
            "Multiple comma-separated addresses / networks may be supplied.",
            self.browser.contents,
        )
        self.assertIn(
            "Invalid IP range: 10.0.5.5/24 has host bits set", self.browser.contents
        )

        self.assertEqual(
            self.browser.getControl(name="form.widgets.ip_range").value,
            "10.0.5.5/24",
        )
        self.assertEqual(self.browser.getControl(name="form.widgets.title").value, "")
        self.assertEqual(
            self.browser.getControl(name="form.buttons.cancel").value, "Cancel"
        )
        self.assertEqual(
            self.browser.getControl(name="form.buttons.save").value, "Save"
        )

        # Assert that readonly widget values are retained as well
        soup = BeautifulSoup(self.browser.contents, "html.parser")
        fields = soup.css.select("form div.field")
        widget_values = [" ".join(f.text.split()) for f in fields]
        self.assertIn(f"User ID {TEST_USER_ID}", widget_values)
        self.assertIn(f"Key ID {service_key['key_id']}", widget_values)
        self.assertIn("Issued 1/7/18 3:30 PM", widget_values)

    def test_edit_key_form_handles_no_changes_being_made(self):
        build_service_key(self.plugin)
        transaction.commit()

        self._login()
        self.browser.open(f"{self.portal_url}/@@manage-service-keys")

        self.browser.getLink("Edit").click()
        self.browser.getControl(name="form.buttons.save").click()

        self.assertIn("No changes were applied.", self.browser.contents)

    def test_edit_key_form_handles_cancelling_edit(self):
        build_service_key(self.plugin)
        transaction.commit()

        self._login()
        self.browser.open(f"{self.portal_url}/@@manage-service-keys")
        self.browser.getLink("Edit").click()

        self.browser.getControl("Cancel").click()

        self.assertIn("Edit cancelled", self.browser.contents)
        self.assertTrue(self.browser.url.endswith("@@manage-service-keys"))

    def test_edit_key_form_doesnt_allow_editing_other_users_key(self):
        service_key = build_service_key(
            self.plugin,
            arguments={
                "title": "Not my key",
                "user_id": "other.user",
            },
        )
        transaction.commit()

        edit_url = f"{self.portal_url}/@@manage-service-keys-edit?key_id={service_key['key_id']}"  # noqa: E501
        self._login()
        self.browser.open(edit_url)

        self.assertIn("Insufficient Privileges", self.browser.contents)


class TestUsageLogsView(FunctionalTestCase):
    layer = FTW_TOKENAUTH_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        self.portal_url = self.portal.absolute_url()
        self.browser = Browser(self.app)
        self.plugin = self.portal.acl_users["token_auth"]

        transaction.commit()

    def _login(self):
        self.browser.open(f"{self.portal_url}/login")
        self.browser.getControl(name="__ac_name").value = TEST_USER_NAME
        self.browser.getControl(name="__ac_password").value = TEST_USER_PASSWORD
        self.browser.getControl(name="buttons.login").click()

    def test_lists_usage_logs(self):
        # Create a service key and issue two access tokens with it
        service_key = build_service_key(self.plugin)

        self.request._client_addr = "10.0.0.77"
        self.request.environ["HTTP_USER_AGENT"] = "some-client/1.23.4"

        with freeze_time(datetime(2018, 1, 1, 15, 30)):
            build_access_token(self.plugin, service_key=service_key)

        with freeze_time(datetime(2018, 1, 5, 12, 45)):
            build_access_token(self.plugin, service_key=service_key)

        transaction.commit()
        self._login()
        self.browser.open(f"{self.portal_url}/@@manage-service-keys")
        soup = BeautifulSoup(self.browser.contents, "html.parser")
        key_rows = soup.css.select("#table-service-keys tbody tr")
        self.assertEqual(1, len(key_rows))

        key_values = soup.css.select("#table-service-keys tbody tr td")
        self.assertEqual(
            "Jan 05, 2018 12:45 PM", key_values[5].get_text().strip()
        )  # Last used

        logs_link_url = key_values[5].select("a")[0].get("href")
        self.browser.open(logs_link_url)

        soup = BeautifulSoup(self.browser.contents, "html.parser")

        logs_table_rows = soup.css.select("#table-usage-logs tbody tr")
        self.assertEqual(len(logs_table_rows), 2)
        first_row = logs_table_rows[0].css.select("td")
        second_row = logs_table_rows[1].css.select("td")

        self.assertEqual(
            [
                "Jan 05, 2018 12:45 PM",
                "test_user_1_",
                "10.0.0.77",
                "some-client/1.23.4",
            ],
            [r.text.strip() for r in first_row],
        )
        self.assertEqual(
            [
                "Jan 01, 2018 03:30 PM",
                "test_user_1_",
                "10.0.0.77",
                "some-client/1.23.4",
            ],
            [r.text.strip() for r in second_row],
        )
