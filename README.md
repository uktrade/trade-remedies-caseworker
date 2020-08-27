# trade-remedies-caseworker
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-8-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->
Case-worker-facing UI for the Trade Remedies system

### Code style

We use the following tools to maintain a consistent coding style

- [black](https://black.readthedocs.io/) - for python code formatting
- [flake8](https://flake8.pycqa.org/en/latest/) - Python code style
- [prettier](https://prettier.io/) - for javascript and sass code formatting

These style rules are enforced by CircleCI *so please check your code locally before pushing changes!*

### Quick code formatting locally

The quickest way is the run via docker containers.

    make docker-code-style
    make frontend-code-style

These will create temporary containers install dependencies and run the code formatters


### Running standalone

It's possible to run the environment as a standalone local app, using virtualenv.
This assumes you have virtualenvwrapper installed, and a virtual env is created (either
via `mkvirtualenv trade-remedies-caseworker` for example).
Use Python 3.6+ as your interpretor.

```
workon trade-remedies-caseworker
./manage.py runserver
```

### Running via Docker

Firstly, you should copy example.env to local.env and add the necessary
environment variables for a local development environment.  local.env is in
.gitignore and should not be committed to the repo.

The caseworker can be brought up using docker-compose.  The API is similarly
available via Docker and should already be running.

```
make docker-cli
```

This will drop you into a terminal session within the container where you can
run the usual commands eg

```
python manage.py runserver_plus 0.0.0.0:8001

python manage.py shell_plus
```

Any changes made to source files on your local computer will be reflected in
the container.


### Full Dockerised environment

The repository at https://github.com/uktrade/trade-remedies-docker contains
a fully dockerised environment containerised and integrated together.
To use it, clone the repository at the same level of the api, caseworker and public
repositories and run `docker-compose-up` to bring it up.
More information is within the repository.


## Deployment

Trade Remedies Case Worker UI configuration is performed via the following environment variables:


| Variable name | Required | Description |
| ------------- | ------------- | ------------- |
| `ALLOWED_HOSTS` | Yes | Comma-separated list of hostnames at which the app is accessible |
| `DEBUG`  | Yes | Whether Django's debug mode should be enabled. |
| `DJANGO_SECRET_KEY`  | Yes | |
| `DJANGO_SETTINGS_MODULE`  | Yes | |
| `TRADE_REMEDIES_API_ROOT_URL`  | Yes | |
| `VCAP_SERVICES` | Yes | [CloudFoundry-compatible ](https://docs.run.pivotal.io/devguide/deploy-apps/environment-variable.html#VCAP-SERVICES)/[GDS PaaS-compatible](https://docs.cloud.service.gov.uk/deploying_apps.html#system-provided-environment-variables) configuration. The connection string at `redis[0].credentials.uri` is used to connect to Redis, which must include the password if required. It should _not_ end a forward slash. |
| `REDIS_DATABASE_NUMBER` | Yes | The database number in the Redis instance connected to by the details in `VCAP_SERVICES`. |


## Cloud Foundry

The following steps will deploy the API to Cloud Foundry.
Make sure to peform the `cf login` or `cf target` to select the org and space.

```
# cf login -a API-HERE -u YOUR-USER-HERE  # Select the org and space
cf set-env traderemediescaseworker DISABLE_COLLECTSTATIC 1  # Temporary
cf set-env traderemediescaseworker DJANGO_SECRET_KEY 'changeme'
cf push
```

## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

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