# For developers

## Prerequisites
You'll need to have poetry installed to manage python dependencies. Instructions for installing poetry can be found [here](https://python-poetry.org/docs/).

To install the CLI locally, run the following commands from the root project directory:
```
poetry lock      # only needed if you updated dependencies in pyproject.toml
poetry install
```
Note: We are currently using Poetry version 1.8.5 - You may need to revert your installed version of Poetry to this version.

You do not need to re-run these commands each time you update code locally, unless you've added dependencies in pyproject.toml.


## Developing
If you do update dependencies in `pyproject.toml`, run `poetry lock` and check in the resulting changes to `poetry.lock` along with the rest of
your code changes. 

If you use an IDE terminal, you can run the following commands from there. To interact with a 
terminal external to your IDE, first run `poetry shell` and then you'll be able to run the 
commands as documented here.

### Tests, linters, and formatting
Install [pre-commit](https://pre-commit.com/):
```bash
pre-commit install
```
This will activate the pre-commit tasks defined in `.pre-commit-config.yaml` on each commit.

To run tests:
```bash
pytest
```

To run tests with a coverage report printed to the terminal:
```bash
pytest --cov-report term --cov=terralab
```

To run the formatter, execute the following command from the root project directory:
```bash
black .
```

To run the linter with fixes, execute the following command from the root project directory:
```bash
ruff check --fix
```
To run the linter as a check without fixes, omit the `--fix` flag.

## Coordinating changes with the Teaspoons service
Sometimes, updates to [Teaspoons](https://github.com/DataBiosphere/terra-scientific-pipelines-service) will need to be coordinated with updates to the CLI. 

To test changes in Teaspoons locally against your local CLI, do the following once you've made changes in your local code and are ready to test them:

1. Follow [the instructions in the Teaspoons repo for creating the autogenerated Python client locally](https://github.com/DataBiosphere/terra-scientific-pipelines-service/blob/main/README.md#testing-the-cli-locally). 
2. In this repo, edit the [pyproject.toml](pyproject.toml) file as follows: comment out the line that defines the `terra-scientific-pipelines-service-api-client` dependency, and add a line like `teaspoons-client = {path = "YOUR/LOCAL/PATH/TO/terra-scientific-pipelines-service/python-client/generated"}`
 It should look something like this:
 ```
 teaspoons-client = {path = "/Users/awesomedeveloper/workbench/terra-scientific-pipelines-service/python-client/generated"}
# terra-scientific-pipelines-service-api-client = "^0.1.0"
```
3. Run `poetry update`. (This is equivalent to running `poetry lock` and then `poetry install`.)

Your CLI should now be importing the `teaspoons_client` via the local code rather than the package from PyPi.

Note: if the locally generated code is not being imported as expected, try deleting and recreating the poetry virtual environment by running the following:
```
rm -rf $(poetry env info --path)
poetry install
```

TODO - Remove this line after release to production! By default the CLI points to the **production** [instance](https://teaspoons.dsde-prod.broadinstitute.org) of Teaspoons. Note that you need to be on the VPN (non-split) to access the production instance.

To run the CLI against your **locally** running instance of Teaspoons:
1. Follow [the instructions in the Teaspoons repo for running the service locally](https://github.com/DataBiosphere/terra-scientific-pipelines-service/blob/main/README.md#local-development). 
2. In this repo, edit the `terralab/.terralab-cli-config` file:
   1. Point the `TEASPOONS_API_URL` to `http://localhost:8080` instead of the live environment deployment of Teaspoons.
   2. Set the `OAUTH_OPENID_CONFIGURATION_URI` and `OAUTH_CLIENT_ID` to point to the appropriate values for the local environment (These values can be found in GSM) 
3. That's it! Run your CLI commands and test until you're confident it's all working as you'd like.

To run the CLI against the **dev** instance of Teaspoons:
1. In this repo, edit the `terralab/.terralab-cli-config` file:
   1. Point the `TEASPOONS_API_URL` to `https://teaspoons.dsde-dev.broadinstitute.org` instead of the live environment deployment of Teaspoons.
   2. Set the `OAUTH_OPENID_CONFIGURATION_URI` and `OAUTH_CLIENT_ID` to point to the appropriate values for the local environment (These values can be found in GSM)
2. That's it! Run your CLI commands and test until you're confident it's all working as you'd like.
