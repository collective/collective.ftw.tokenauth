# tokenauth 🚀

[![Built with Cookieplone](https://img.shields.io/badge/built%20with-Cookieplone-0083be.svg?logo=cookiecutter)](https://github.com/plone/cookieplone-templates/)
[![Black code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CI](https://github.com/collective/tokenauth/actions/workflows/main.yml/badge.svg)](https://github.com/collective/tokenauth/actions/workflows/main.yml)

PAS plugin that facilitates **machine-to-machine authentication** by
implementing a two legged OAuth2 flow using service keys and short-lived
access tokens.

This project is a fork of the original [ftw.tokenauth](https//github.com/4teamwork/ftw.tokenauth) package by 4teamwork, released under the GPLv2.

## Documentation

The documentation of this package can be found on [read-the-docs](https://collectiveftwtokenauth.readthedocs.io/en/)


## Project structure 🏗️

This monorepo consists of the following distinct sections:

- **backend**: Houses the Plone backend add-on in package named collective.ftw.tokenauth.
- **frontend**: Contains the React (Volto) package named volto-tokenauth
- **docs**: Documentation

### Why this structure? 🤔

- All necessary codebases to run the site are contained within the repository (excluding existing add-ons for Plone and React).
- Specific GitHub Workflows are triggered based on changes in each codebase (refer to .github/workflows).
- Simplifies the creation of Docker images for each codebase.
- Demonstrates Plone installation/setup without buildout.

## Code quality assurance 🧐

To check your code against quality standards, run the following shell command.

```shell
make check
```

### Format the codebase

To format and rewrite the code base, ensuring it adheres to quality standards, run the following shell command.

```shell
make format
```

| Section | Tool | Description | Configuration |
| --- | --- | --- | --- |
| backend | Ruff | Python code formatting, imports sorting  | [`backend/pyproject.toml`](./backend/pyproject.toml) |
| backend | `zpretty` | XML and ZCML formatting  | -- |
| frontend | ESLint | Fixes most common frontend issues | [`frontend/.eslintrc.js`](.frontend/.eslintrc.js) |
| frontend | prettier | Format JS and Typescript code  | [`frontend/.prettierrc`](.frontend/.prettierrc) |
| frontend | Stylelint | Format Styles (css, less, sass)  | [`frontend/.stylelintrc`](.frontend/.stylelintrc) |

Formatters can also be run within the `backend` or `frontend` folders.

### Linting the codebase
or `lint`:

 ```shell
make lint
```

| Section | Tool | Description | Configuration |
| --- | --- | --- | --- |
| backend | Ruff | Checks code formatting, imports sorting  | [`backend/pyproject.toml`](./backend/pyproject.toml) |
| backend | Pyroma | Checks Python package metadata  | -- |
| backend | check-python-versions | Checks Python version information  | -- |
| backend | `zpretty` | Checks XML and ZCML formatting  | -- |
| frontend | ESLint | Checks JS / Typescript lint | [`frontend/.eslintrc.js`](.frontend/.eslintrc.js) |
| frontend | prettier | Check JS / Typescript formatting  | [`frontend/.prettierrc`](.frontend/.prettierrc) |
| frontend | Stylelint | Check Styles (css, less, sass) formatting  | [`frontend/.stylelintrc`](.frontend/.stylelintrc) |

Linters can be run individually within the `backend` or `frontend` folders.

## Internationalization 🌐

Generate translation files for Plone and Volto with ease:

```shell
make i18n
```

## Credits and acknowledgements 🙏

4teamwork for the original code of [ftw.tokenauth](https://github.com/4teamwork/ftw.tokenauth)

Generated using [Cookieplone (0.9.10)](https://github.com/plone/cookieplone) and [cookieplone-templates (96574af)](https://github.com/plone/cookieplone-templates/commit/96574af4136cae375cc74be36daed12df6ed6f82) on 2025-12-19 16:10:59.558520. A special thanks to all contributors and supporters!
