from collective.ftw.tokenauth.pas.storage import CredentialStorage
from collective.ftw.tokenauth.service_keys.key_generation import create_service_key_pair
from plone.app.testing import TEST_USER_ID

import jwt
import time


def build_key_pair(arguments=None):
    if arguments is None:
        arguments = {}
    private_key, service_key = create_service_key_pair(
        arguments.get("user_id", TEST_USER_ID),
        arguments.get("title"),
        arguments.get("token_uri"),
        arguments.get("ip_range"),
    )
    # Override the randomly created client_id
    service_key["client_id"] = arguments.get("client_id")

    return private_key, service_key


def build_jwt_grant(keypair, arguments=None, without_claims=None):
    """build a JWT grant for tests"""
    if arguments is None:
        arguments = {}
    if without_claims is None:
        without_claims = []

    private_key, service_key = keypair

    # Determine defaults for required claims
    aud = arguments.get("aud", service_key["token_uri"])
    iss = arguments.get("iss", service_key["client_id"])
    sub = arguments.get(
        "sub",
        service_key["user_id"],
    )
    iat = arguments.get("iat", int(time.time()))
    exp = arguments.get("exp", int(time.time()) + (60 * 60))

    claim_set = {
        "aud": aud,
        "iss": iss,
        "sub": sub,
        "iat": iat,
        "exp": exp,
    }

    # nbf and scope claims are not supported. So they're not included in
    # the claimset by default unless specifically requested

    nbf = arguments.get("nbf")
    if nbf:
        claim_set["nbf"] = nbf

    scope = arguments.get("scope")
    if scope:
        claim_set["scope"] = scope

    # Drop any claims that have been requested to be omitted
    if without_claims:
        for claim in without_claims:
            claim_set.pop(claim)

    grant_token = jwt.encode(claim_set, private_key, algorithm="RS256")
    return grant_token


def build_service_key(plugin, arguments=None):
    if arguments is None:
        arguments = {}
    key_pair = plugin.issue_keypair(
        arguments.get("user_id", TEST_USER_ID),
        arguments.get("title", "Default Title"),
        arguments.get("ip_range"),
    )

    return key_pair[1]


def build_access_token(plugin, service_key=None, arguments=None):
    if arguments is None:
        arguments = {}

    if service_key is None:
        service_key = build_service_key(
            plugin,
            arguments={
                "user_id": arguments.get("user_id", TEST_USER_ID),
                "title": "Test Key",
            },
        )

    access_token = plugin.issue_access_token(
        service_key["key_id"], service_key["user_id"]
    )
    issued_at = arguments.get("issued_at")
    if issued_at:
        # Set issue date of token in storage
        storage = CredentialStorage(plugin)
        token_in_storage = storage.get_access_token(access_token["token"])
        token_in_storage["issued"] = issued_at

    return access_token
