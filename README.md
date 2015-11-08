# obi
```
obi is a command-line tool for working with gspeak projects.

Available tasks:

build             Builds the project (optionally, on numerous machines)
clean             Clean the build directory (optionally, on numerous machines)
go                Build, stop, and run the project (optionally, on numerous machines)
ls                List obi templates
new               Generate project scaffolding based on a obi template
stop              Stops the application (optionally, on numerous machines)
template install  Install an obi template
template remove   Remove an installed obi template
template upgrade  Upgrade an installed obi template

Edit project.yaml (in your project folder) to configure sets of machines for
go/stop, set arguments for building and launching the program, choose feld &
screen proteins, and set the names of pools that your program will use.

Usage:
  obi new <template> <name> [--template_home=<path>] [--g_speak_home=<path>]
  obi go [<room>] [--debug=<debugger>] [--] [<extras>...]
  obi stop [<room>]
  obi clean [<room>]
  obi build [<room>]
  obi ls [--template_home=<path>]
  obi template install <giturl> [<name>] [--template_home=<path>]
  obi template remove <name> [--template_home=<path>]
  obi template upgrade <name> [--template_home=<path>]
  obi -h | --help | --version

Options:
  -h --help               Show this screen.
  --version               Show version.
  --g_speak_home=<path>   Optional: absolute path of g-speak dir to build against.
  --template_home=<path>  Optional: path containing installed obi templates.
  --debug=<debugger>      Optional: launches the application in a debugger.
```

* [Install](#install)
  - [Mac](#mac)
  - [Ubuntu](#ubuntu)
* [project.yaml](#projectyaml)
* [Templates](#templates)
* [Distribution](#distribution)
* [Example](#example)
* [Tasks](#tasks)
* [Editor tips](#editor-tips)

## Install

### Mac

#### Homebrew
```bash
# Install homebrew
ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

# Add the Oblong/homebrew-tools tap @ github.com/Oblong/homebrew-tools
brew tap Oblong/homebrew-tools

# Install
brew install obi

# Upgrading
brew update
brew upgrade obi
```

### Ubuntu

First, install `python-setuptools`:

```bash
sudo apt-get install python-setuptools
```

Ensure this is on your `PATH`:

```bash
export PATH=$HOME/.local/bin:$PATH
```

#### Ubuntu 14.04

On Ubuntu 14.04, you can install both `pip` and `obi` to your home directory.

Install `pip` and then `obi`:

```bash
easy_install --user pip
pip install --user git+ssh://git@gitlab.oblong.com/solutions/obi.git
```

#### Ubuntu 12.04

On Ubuntu 12.04, you must install `pip` systemwide but can install `obi` to
your home directory.

Install `pip` with `sudo`:

```bash
sudo easy_install pip
```

And update `setuptools` and `distribute` packages:

```bash
sudo pip install --upgrade setuptools
sudo pip install --upgrade distribute
```

Finally, install `obi`:

```bash
pip install --user git+ssh://git@gitlab.oblong.com/solutions/obi.git
```

## project.yaml

Todo(jshrake): document the keys of `project.yaml`

## Templates

### Installing

Install any template from a git repo
```
obi template install git@gitlab.oblong.com:obi/greenhouse
obi template install git@gitlab.oblong.com:obi/yovo
obi template install git@gitlab.oblong.com:obi/rad
```

The install command clones the specified repo to
`~/.local/share/oblong/obi` (or `${XDG_DATA_HOME}/oblong/obi` if that
environment variable is set). Feel free to manage this directory
yourself!

### Upgrading

```
obi template upgrade greenhouse
obi template upgrade yovo
obi template upgrade rad
```

Runs `git pull` in the appropriate repository.

### Removing

```
obi remove greenhouse
obi remove yovo
obi remove rad
```

Removes the directory.

# Distribution

Make sure to update the `version` in [setup.py](setup.py)! See http://semver.org/
```bash
cd obi
# you may need to install wheel first
# pip install wheel
pip wheel .
```

This will generate a directory `wheelhouse` that contains all the obi wheel along with wheels for all of the dependencies. Tarball this directory and ship it out to the world. Users on the other end can untar it and

```bash
pip install --find-links /path/to/untared/wheelhouse oblong-obi
```

## Example

```bash
# create a new greenhouse project based on gspeak 3.19
obi new greenhouse appname --g_speak_home=/opt/oblong/g-speak3.19
cd appname
# build and run the application locally
obi go
# build and run the application on the hex and wall
# see the project.yaml file for where hex and wall are
# defined
obi go hex
obi go wall
# stop the application
obi stop hex
obi stop wall
```

## Tasks

### obi new [template] [name]
---

`obi new <template> <name>` generates project scaffolding based on a template in your current working directory. Currently, the only templates shipped with obi are [greenhouse](obi/new/greenhouse/greenhouse.py), [rad](obi/new/rad/rad.py), and [yovo](obi/new/yovo/yovo.py).

The user can create and install additional templates for obi to use. An example of this is the template for starting new IBM projects found at [obi-seabed](https://gitlab-ibm.oblong.com/seabed/obi-seabed). After installing this template, you can create new IBM projects as `obi new seabed my-cool-ibm-project`.

`obi ls` returns a list of all available obi templates installed on this machine.

#### options
- `[--g_speak_home=<path>]`: Builds the project against the specified g-speak. Path must be an absolute path to the g-speak home directory.

If the `--g_speak_home` option is not specified, obi attempts to find a default version of gspeak that will work well for your system. It will look for the `G_SPEAK_HOME` environment variable, and finally fallback to extracting for the highest version g-speak found in `/opt/oblong/`.

#### example
```bash
obi new greenhouse app-name --g_speak_home=/opt/oblong/g-speak3.19
```

### obi ls
---
`obi ls` Returns a list of installed obi templates available for use with the `new` task.

#### example
```bash
obi ls
```

## Fabric Tasks

'obi [go | stop | build | clean] [room-name]' are aliases for [`fab room:[room-name][go | stop | build | clean]`](http://www.fabfile.org/). The logic for each task is implemented entirely in the [task.py](obi/task/task.py). If `room-name` is specified, the task is executed on the host machines listed under the associated room in [project.yaml](obi/templates/project.yaml). If `room-name` is not specified, the task is executed on the local machine.

### obi go [room-name]
---
`obi go [room-name]` builds and runs the application. If no room name is specified, then this task is performed locally (see the `localhost` map in [project.yaml](obi/templates/project.yaml)). If `room-name` is specified, it must match one of the keys listed under the `rooms` map in [project.yaml](obi/templates/project.yaml). The implementation details of how the application is built and launched, both locally and remotely, are in the [fabfile](obi/templates/fabfile.py) (see the definitions of `go`, `local_go` and `remote_go`).


#### example

```bash
# Launch the application on the local machine
obi go
# Launch application on the host machines listed under wall
obi go wall
```

### obi stop [room-name]
---
`obi stop [<name>]` kills the application on the remote set of hosts specified by `<name>`. The `<name>` specified must match one of the keys listed under the `rooms` map in [project.yaml](obi/templates/project.yaml). This is equivalent to running `pkill -KILL app-name` on each of the remote hosts. If no name is specified, then the application is stopped on the local machine.

#### example
```bash
# Stop the application on the local machine
obi stop
# Stop the application on the host machines listed under hex
obi stop hex
```

### obi build [room-name]
---
`obi build [room-name]` Builds the application

#### example
```bash
# Build the application on the local machine
obi build
# Build the application on the host machines listed under hex
obi build hex
```

### obi clean [room-name]
---
'obi clean [room-name]' cleans the build directory

#### example
```bash
# Clean the application build directory on the local machine
obi clean
# Clean the application build directory on the host machines listed under hex
obi clean hex
```

## Editor tips

### emacs

obi works well out of the box with emacs's
[compilation][emacs-compilation] feature.  `M-x compile<RET>obi go
[room-name]` from a file in the root directory of the project will run
obi as a subprocess of emacs and pipe the output to a `*compilation*`
buffer (which can support obi's use of
[ANSI colors][colorize-compilation]).  Compile errors are picked up by
emacs, and you can navigate directly to the error's location using the
ordinary features of [compilation mode][emacs-comp-mode].  To kill an
obi invocation in the compilation buffer, use `M-x kill-compilation`.

[emacs-compilation]: http://www.gnu.org/software/emacs/manual/html_node/emacs/Compilation.html
[emacs-comp-mode]: http://www.gnu.org/software/emacs/manual/html_node/emacs/Compilation-Mode.html
[colorize-compilation]: http://stackoverflow.com/a/3072831/692055
