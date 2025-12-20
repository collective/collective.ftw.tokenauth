# collective.ftw.tokenauth

This project is a fork of the original [ftw.tokenauth](https://github.com/4teamwork/ftw.tokenauth) product.

It has been updated to support python3 and Plone 6.

PAS plugin that facilitates **machine-to-machine authentication** by
implementing a two legged OAuth2 flow using service keys and short-lived
access tokens.

## Installation

Add collective.ftw.tokenauth to your dependencies.

## Configuration

For a user to be allowed to issue (or otherwise manage) service keys, they
require the `ftw.tokenauth: Manage own Service Keys` permission. So
integration packages need to assign this permission to roles that should be
allowed to use service keys.

By default all users with the "Member" role get this permission.

## Contribute

- [Issue tracker](https://github.com/collective/tokenauth/issues)
- [Source code](https://github.com/collective/tokenauth/)

### Prerequisites ✅

- An [operating system](https://6.docs.plone.org/install/create-project-cookieplone.html#prerequisites-for-installation) that runs all the requirements mentioned.
- [uv](https://6.docs.plone.org/install/create-project-cookieplone.html#uv)
- [Make](https://6.docs.plone.org/install/create-project-cookieplone.html#make)
- [Git](https://6.docs.plone.org/install/create-project-cookieplone.html#git)
- [Docker](https://docs.docker.com/get-started/get-docker/) (optional)

### Installation 🔧

1.  Clone this repository.

    ```shell
    git clone git@github.com:collective/tokenauth.git
    cd tokenauth/backend
    ```

2.  Install this code base.

    ```shell
    make install
    ```

### Add features using `plonecli` or `bobtemplates.plone`

This package provides markers as strings (`<!-- extra stuff goes here -->`) that are compatible with [`plonecli`](https://github.com/plone/plonecli) and [`bobtemplates.plone`](https://github.com/plone/bobtemplates.plone).
These markers act as hooks to add all kinds of features through subtemplates, including behaviors, control panels, upgrade steps, or other subtemplates from `bobtemplates.plone`.
`plonecli` is a command line client for `bobtemplates.plone`, adding autocompletion and other features.

To add a feature as a subtemplate to your package, use the following command pattern.

```shell
make add <template_name>
```

For example, you can add a content type to your package with the following command.

```shell
make add content_type
```

You can add a behavior with the following command.

```shell
make add behavior
```

```{seealso}
You can check the list of available subtemplates in the [`bobtemplates.plone` `README.md` file](https://github.com/plone/bobtemplates.plone/?tab=readme-ov-file#provided-subtemplates).
See also the documentation of [Mockup and Patternslib](https://6.docs.plone.org/classic-ui/mockup.html) for how to build the UI toolkit for Classic UI.
```

## License

The project is licensed under GPLv2.

## Credits and acknowledgements 🙏

Generated from the [`cookieplone-templates` template](https://github.com/plone/cookieplone-templates/tree/main/) on 2025-12-19 15:11:56.. A special thanks to all contributors and supporters!
