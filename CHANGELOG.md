# Changelog

All notable changes to this project will be documented in this file with the following template:

### Added
- New features.

### Changed
- Updates and improvements.

### Fixed
- Bug fixes.

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
