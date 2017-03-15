# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/).
This project does not use semver.

## [Unreleased]
### Added
- Add logging of commands to systemd journal on remote machines

## [3.2.0] - 2016-01-26
### Added
- Add changelog
- Add new property, `rsync-extra-opts`, in project.yaml to specify rsync arguments for `obi rsync`

### Changed
- Change `obi ls` to `obi template list`

### Fixed
- Change fabric version (1.10.2 => 1.10.3) to fix pycrypto issue
- Improve code that searches for and sets G_SPEAK_HOME
- Fix trailing .git in template name
- Fix behavior when obi is invoked in a subdirectory of the project folder

## [3.1.0] - 2016-06-23
### Added
- Add a new command, `obi fetch`, for fetching files and directories from remote machines.

### Removed
- Remove the feature that generated obi-*.sh files on command execution.

### Fixed
- Fix error message for `obi template upgrade` on nonexistent template name
- Fix rsync bug when directory name doesn't match project name
- Fix rsync bug when remote target doesn't already have the destination folder
