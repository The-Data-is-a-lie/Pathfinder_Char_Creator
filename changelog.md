# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--
Categories (use only the ones you need, in this order):
  Added       — new features
  Changed     — changes to existing functionality
  Deprecated  — soon-to-be-removed features
  Removed     — now-removed features
  Fixed       — bug fixes
  Security    — vulnerability fixes
On release: rename "[Unreleased]" to "[x.y.z] - YYYY-MM-DD" and start a fresh Unreleased block.
-->

## [Unreleased]

### Added
- `class_feat_labels` in the `/update_character_data` response: each class bonus feat is tagged with
  its granting class and level (e.g. "Fighter 1") via a new `class_bonus_feat_levels()` schedule
  helper, so the sheet can show class feats as "Fighter 1: Weapon Focus".

### Fixed
- `skill_ranks` is no longer double-JSON-encoded in the `/update_character_data` response, so the
  FoundryVTT module can read the generated skill ranks (they previously arrived as an un-parseable string).
