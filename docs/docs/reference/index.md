---
myst:
  html_meta:
    "description": "tokenauth Reference"
    "property=og:description": "tokenauth Reference"
    "property=og:title": "tokenauth Reference"
    "keywords": "Plone, _tokenauth,_ reference"
---

# Authentication flow


The authentication flow involves four steps:

1. A logged in service user issues a service key in Plone, and stores the
   private key in a safe location accessible to the client application.

2. The client application uses the private key to create and sign a JWT
   authorization grant.

3. The client application exchanges the JWT authorization grant for a
   short-lived access token at the ``@@oauth2-token`` endpoint.

4. The client then uses this access token to authenticate requests to
   protected resources.


Assuming the client is in possession of a service key, the flow looks like this:


![Authentication flow diagram](/_static/authentication-flow.png)

## Recommended Client Implementation


The recommended logic to implement on a client to repeatedly authenticate and
obtain new access tokens looks something like this:

![Client Flow](/_static/client-flow.png)

Image Source: https://drive.google.com/open?id=1wVua7R5VQUxJKGL8dq1kGV4AjLgjGSXZ

The client should, instead of trying to predict access token expiration, just
anticipate the case that authentication using an existing token will fail
(because the token expired), and then perform the necessary steps to obtain
a new token.

To accomplish this, it is recommended to delegate all the requests a client
application wants to make to a class that expects an ``Access token expired``
response as described above, and obtains a new token if necessary. The failed
request that lead to the error response then needs to be re-dispatched with
its original parameters, but then new token in the ``Authorization`` header.

Care needs to be taken to **not** include an expired token (or any
``Authorization`` header for that matter) with the requests to the token
endpoint when obtaining a new token.

An example implementation in Python can be found in
[client-example.py](/_static/client-example.py)