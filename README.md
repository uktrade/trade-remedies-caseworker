# trade-remedies-caseworker
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-8-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->
[![codecov](https://codecov.io/gh/uktrade/trade-remedies-caseworker/branch/develop/graph/badge.svg)](https://codecov.io/gh/uktrade/trade-remedies-caseworker/)
Case-worker-facing UI for the Trade Remedies system

## Code Style

Live Services Team use [Black](https://black.readthedocs.io/en/stable/index.html) for python code formatting and
[flake8](https://flake8.pycqa.org/en/latest/) for code analysis. 

This project uses prettier - https://prettier.io/ - for javascript and sass code formatting

## Development

#### Set up

Firstly, you should copy local.env.example to local.env and add the necessary environment variables for a local development environment.  local.env is in .gitignore and should not be committed to the repo.

Populate the following environment variables in the local.env file:

| Variable name | Required | Description |
| ------------- | ------------- | ------------- |
| `S3_BUCKET_NAME` | Yes | S3 bucket name of bucket used for local dev |
| `S3_STORAGE_KEY`  | Yes | AWS access key ID |
| `S3_STORAGE_SECRET`  | Yes | AWS secret access key | |
| `AWS_REGION`  | Yes | Change if different from "eu-west-2" |
| `ORGANISATION_NAME` | Yes | Name for the organisation |
| `ORGANISATION_INITIALISM` | Yes | Initials for the organisation |

If you are not sure what to use for one of the values above, ask a colleague or contact the SRE team.

#### Running the project

This project should be run using the Trade Remedies orchestration project available at: https://github.com/uktrade/trade-remedies-docker

## Compiling requirements

We use pip-compile from https://github.com/jazzband/pip-tools to manage pip dependencies. This runs from the make file when generating requirements:

Run `make all-requirements`

This needs to be run from the host machine as it does not run in a container.

## Front end
In order to run prettier on the front end part of this project, in the orchestration project run:
 
```
make frontend-code-style
```

## BDD testing

Behavioural testing is provided by [Behave Django](https://github.com/behave/behave-django) and can be triggered by running:

`make bdd`

from the Trade Remedies orchestration project directory.

You can make test objects available for BDD testing by creating views that create them in the 'api_test' app in the [Trade Remedies API](https://github.com/uktrade/trade-remedies-api) project.

For more information on the setup of BDD tests see the readme at https://github.com/uktrade/trade-remedies-docker

## Running End to End tests using playwright with pytest
Playwright documentation - https://playwright.dev/python/docs/api/class-playwright

The end-to-end frontend tests reside in the e2e directory and are designed to operate independently of the rest of the application. This autonomy is facilitated through a local pytest.ini configuration file located within the same directory. The pytest.ini file configures specific parameters and settings essential for the execution of these tests, ensuring they can run in a self-contained environment. For detailed customization options and further information on pytest configuration files, refer to the [pytest configuration docs](https://docs.pytest.org/en/7.0.x/reference/customize.html)

If you are running the docker build

1. Ensure the API is running & the frontend service is runing and can be accessed on `http://localhost:{frontend_port}` if runing within the docker container

2. Ensure the frontend server is up and has reached the point where the Django development server is running.

By default the tests DO NOT RUN in headless mode, to activate headless mode the variable --is-headless will be required.

*NOTE: Before running the end to end test pipeline we will need setup the below environment variable:*
```bash
TEST_USER_EMAIL = "<email-account-used-to-signup-to-public>"
TEST_USER_PASSWORD = "<password>"
TEST_REPR_INVITE_CASE_ID = "<case-id>"
TEST_REPR_COMPANY_NAME = "<representitive-company-name>"
```

3. Run the tests:
`make test-end-to-end target_url=<target-url>` e.g target_url: `http://localhost:8001/` or `https://trade-remedies-caseworker-uat.london.cloudapps.digital/`

4. To run a specific suite of frontend tests, specify the desired module:
`make test-end-to-end target_url=<target-url> target=test_examples.py`

To run headless:
`make test-end-to-end target_url=http://localhost:8001/ is-headless=true`

#### setup pytest & playwright end to end module

___module structure___

```
e2e/
├── .gitignore # Specifies intentionally untracked files to ignore
├── requirements.txt # Project dependencies
├── conftest.py # the pytest config file (the most important file to get things going)
├── README.md # The top-level README for developers using this project
└── pytest.ini # Configuration file for pytest
└── utils.py # utility functions for the test suite
└── test_file.py # one test file for a specific end to end functionality
└── .e2e.env # required for tests that require environment variables
...
```

## Fitness Functions
![Current fitness metrics for TRSV2](fitness/fitness_metrics_graph.png)

## Contributors ✨

Thanks goes to these wonderful people who contributed to the original private repo ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tr>
    <td align="center"><a href="https://github.com/bobmeredith"><img src="https://avatars2.githubusercontent.com/u/11422209?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Robert Meredith</b></sub></a><br /><a href="https://github.com/uktrade/trade-remedies-caseworker/commits?author=bobmeredith" title="Code">💻</a> <a href="#design-bobmeredith" title="Design">🎨</a></td>
    <td align="center"><a href="http://www.harelmalka.com/"><img src="https://avatars3.githubusercontent.com/u/985978?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Harel Malka</b></sub></a><br /><a href="https://github.com/uktrade/trade-remedies-caseworker/commits?author=harel" title="Code">💻</a> <a href="https://github.com/uktrade/trade-remedies-caseworker/commits?author=harel" title="Documentation">📖</a> <a href="https://github.com/uktrade/trade-remedies-caseworker/pulls?q=is%3Apr+reviewed-by%3Aharel" title="Reviewed Pull Requests">👀</a></td>
    <td align="center"><a href="https://github.com/ulcooney"><img src="https://avatars0.githubusercontent.com/u/1695475?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Paul Cooney</b></sub></a><br /><a href="https://github.com/uktrade/trade-remedies-caseworker/commits?author=ulcooney" title="Code">💻</a></td>
    <td align="center"><a href="https://github.com/krishnawhite"><img src="https://avatars1.githubusercontent.com/u/5566533?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Krishna White</b></sub></a><br /><a href="https://github.com/uktrade/trade-remedies-caseworker/commits?author=krishnawhite" title="Code">💻</a></td>
    <td align="center"><a href="http://charemza.name/"><img src="https://avatars1.githubusercontent.com/u/13877?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Michal Charemza</b></sub></a><br /><a href="https://github.com/uktrade/trade-remedies-caseworker/commits?author=michalc" title="Code">💻</a> <a href="https://github.com/uktrade/trade-remedies-caseworker/pulls?q=is%3Apr+reviewed-by%3Amichalc" title="Reviewed Pull Requests">👀</a></td>
    <td align="center"><a href="https://github.com/nao360"><img src="https://avatars3.githubusercontent.com/u/6898065?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Nao Yoshino</b></sub></a><br /><a href="https://github.com/uktrade/trade-remedies-caseworker/commits?author=nao360" title="Code">💻</a></td>
    <td align="center"><a href="https://github.com/ravatapalli"><img src="https://avatars0.githubusercontent.com/u/36473779?v=4?s=100" width="100px;" alt=""/><br /><sub><b>ravatapalli</b></sub></a><br /><a href="https://github.com/uktrade/trade-remedies-caseworker/commits?author=ravatapalli" title="Code">💻</a></td>
  </tr>
  <tr>
    <td align="center"><a href="http://blog.clueful.com.au/"><img src="https://avatars0.githubusercontent.com/u/309976?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Brendan Quinn</b></sub></a><br /><a href="https://github.com/uktrade/trade-remedies-caseworker/commits?author=bquinn" title="Code">💻</a></td>
  </tr>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->
<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!
