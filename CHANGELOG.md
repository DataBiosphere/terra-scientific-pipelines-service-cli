# Changelog

All notable changes to this project will be documented in this file with the following template:

### Added
- New features.

### Changed
- Updates and improvements.

### Fixed
- Bug fixes.

## [3.1.0] - 2026-02-25

### Added
- `terralab submit` now accepts either local or Google Cloud Storage hosted input files. 

## [3.0.0] - 2026-01-15

### Changed
- `terralab download` error messages for non-successful runs and runs with expired outputs have changed. This change was part of updating the CLI to use new service API versions: `api/pipelineruns/v2/result/{jobId}` and `api/pipelineruns/v2/result/{jobId}/output/signed-urls`, as `api/pipelineruns/v1/result/{jobId}` is now deprecated.

## [2.1.0] - 2025-12-17

### Added
- `terralab jobs details` output now includes the input parameters provided by the user (including default values if optional inputs were not specified), as well as the input size, when available.

## [2.0.0] - 2025-11-17

### Changed
- `terralab jobs list` output improvements:
  - Added output expiration date which will be displayed under Output Expires column (when available)
  - Removed the Completed timestamp
  - Pipeline Name and Version columns combined into a single Pipeline column
  - Simplified timestamp formatting by removing seconds and explicit timezone information.
    - _Note: All timestamps will continue to reflect the system’s local timezone._
- Timestamps in `terralab jobs details` output will no longer show seconds information.

## [1.2.1] - 2025-10-20

### Changed
- Files uploaded while submitting a job are now limited to a maximum size of 50GB.

## [1.2.0] - 2025-10-17

### Added
- Added pipeline input and output descriptions to `terralab pipelines details` command.

## [1.1.3] - 2025-10-09

### Changed
- Updated the jobs list command to use the v2 API endpoint. The functionality of the command is unchanged.

## [1.1.2] - 2025-10-09

### Added
- Added automatic version checking. Users will be notified if a newer version of terralab is available.

## [1.1.1] - 2025-10-02

### Fixed
- Better handling of 401 Unauthorized errors.

## [1.1.0] - 2025-09-17

### Added
- Added pipeline outputs to `terralab pipelines details` command.

### Changed
- Moved a job's quota consumed from the `terralab jobs list` output table to the `terralab jobs details` output.

## [1.0.8] - 2025-08-27

### Fixed
- Removed auto-opening of authentication URL in `terralab login` command to avoid errors in remote environments.

## [1.0.7] - 2025-08-21

### Added
- Initial release.
