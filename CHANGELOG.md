# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/).
This project does not use semver.

## [3.4.2] - 2017-07-10

### Added
- Add --all flag to obi template upgrade, which upgrades all installed templates [[5ef8494](https://github.com/Oblong/obi/commit/5ef849444f8c3bf9b0ed89e0ff50deec3fbebb17)]

## [3.4.0] - 2017-06-19

### Changed
- cmake-args are now shell escaped

### Fixed
- CMakeFiles are regenerated when cmake-args changes

## [3.3.0] - 2017-05-15
### Added
- Add command completion for bash
- Add optional flag --force (-f for short) to `obi stop` to send a SIGKILL message instead of the usual SIGTERM
- Add new command `obi room list` that lists configured rooms
- Add asciidoc documentation, used to generate `obi.1` roff manpage

### Fixed
- Add shell escaping to arguments passed to shell invocations
- Prevent rerunning cmake when unnecessary by using a sentinel file in the build folder

## [3.2.0] - 2017-01-26
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
