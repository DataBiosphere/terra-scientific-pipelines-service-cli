# Terralab CLI

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=DataBiosphere_terra-scientific-pipelines-service-cli&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=DataBiosphere_terra-scientific-pipelines-service-cli)

## Overview
The terralab CLI provides a command-line interface with which to interact with the [Broad DSP Scientific Pipelines Service](https://github.com/DataBiosphere/terra-scientific-pipelines-service/blob/main/README.md).

Currently, terralab supports running [Array Imputation](https://allofus-anvil-imputation.terra.bio/). For more information about Array Imputation, see our [documentation](https://broadscientificservices.zendesk.com/hc/en-us/articles/39901941351323).

Find instructions on using this CLI [here](https://broadscientificservices.zendesk.com/hc/en-us/articles/39901313672859).

Note that in order to use terralab and the Scientific Pipelines Service, you must have a [Terra](https://services.terra.bio/) account.

## Prerequisites
Your system must run Python 3.12+.

## Installation
You can install the terralab CLI [from PyPi](https://pypi.org/project/terralab-cli/) using your favorite package management tool. 

For example, run
```bash
pip install terralab-cli
```

## Using the CLI
Once installed, to run the CLI, run the following command:
```bash
terralab COMMAND [ARGS]
```

For example, to list the pipelines you can run using Terralab, run the following command:
```bash
terralab pipelines list
```

## For Developers
See [CONTRIBUTING.md](CONTRIBUTING.md) for details on local development setup.

## Changelog
See [CHANGELOG.md](https://github.com/DataBiosphere/terra-scientific-pipelines-service-cli/blob/main/CHANGELOG.md)
