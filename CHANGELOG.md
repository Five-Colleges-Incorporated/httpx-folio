# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Please see [MIGRATING.md](./MIGRATING.md) for information on breaking changes.

## [Unreleased]

### Added

### Fixed

### Changed

### Removed

## [0.2.2] - September 2025

### Fixed
- Add py.typed file

## [0.2.1] - September 2025

### Fixed
- Fix offset paging to allow for non-id columns
- Fix default_client_factory when urls with trailing slashes are passed

## [0.2.0] - September 2025

### Added
- HTTPX QueryParameter standardization and generation for common FOLIO scenarios.

## [0.1.0] - August 2025

The initial release.

### Added
- A resilient HTTPX Client factory for synchronous single tenant FOLIO instances.
- A custom synchronous HTTPX Authentication scheme for FOLIO Refresh Token Auth.
