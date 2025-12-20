from collective.ftw.tokenauth import _
from collective.ftw.tokenauth.pas.ip_range import InvalidIPRangeSpecification
from collective.ftw.tokenauth.pas.ip_range import parse_ip_range
from plone import api
from plone.supermodel import model
from z3c.form.form import Form
from zope import schema
from zope.interface import Invalid


def valid_ip_range(value):
    """Form validator that checks for a valid IP range specification."""
    try:
        parse_ip_range(value)
    except InvalidIPRangeSpecification as exc:
        raise Invalid(
            _(
                "Invalid IP range: ${ip_range_error}",
                mapping={"ip_range_error": str(exc)},
            )
        ) from exc
    return True


class IKeyMetadataSchema(model.Schema):
    """ """

    title = schema.TextLine(
        title=_("label_title", default="Title"),
    )

    key_id = schema.TextLine(
        title=_("label_key_id", default="Key ID"),
        readonly=True,
    )

    user_id = schema.TextLine(
        title=_("label_user_id", default="User ID"),
        readonly=True,
    )

    issued = schema.Datetime(
        title=_("label_issued", default="Issued"),
        readonly=True,
    )

    ip_range = schema.TextLine(
        title=_("label_ip_range", default="IP Range"),
        required=False,
        constraint=valid_ip_range,
        description=_(
            "Allowed IP range specification in "
            '<strong><a href="https://en.wikipedia.org/wiki/Classless_Inter-Domain_Routing#CIDR_notation">'
            "CIDR notation</a></strong>. "
            "Multiple comma-separated addresses / networks may be supplied."
        ),
    )


class BaseForm(Form):
    ignoreContext = True

    @property
    def portal_url(self):
        return api.portal.get().absolute_url()

    @property
    def main_url(self):
        return self.portal_url + "/@@manage-service-keys"

    def get_plugin(self):
        acl_users = api.portal.get().acl_users
        return acl_users["token_auth"]

    def update(self):
        self.request.set("disable_border", True)
        super().update()
