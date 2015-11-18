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
  obi rsync [<room>]
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
* [Templates](#templates)
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

```bash
pip install --user git+ssh://git@github.com/Oblong/obi.git
```
## Templates

### Installing

Install templates from a git repository:
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

Removes the template.

## Tasks

### obi new [template] [name]
---

`obi new <template> <name>` generates project scaffolding based on an installed template in your current working directory.

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

### obi go [room-name]
---
`obi go [room-name]` builds and runs the application. If `<room-name>` is not specified, then the application is built and ran on the local machine.

#### options
- `[--debug=<debugger>]`: Specify a toolname to launch the application. This is useful for launching the application with debuggers or profilers:
```bash
obi go --debug="lldb --"
obi go --debug="strace --" roomname
obi go --debug="gdb -ex run --args" roomname
```

Users can specify special names debuggers in the `project.yaml`

```yaml
# Debuggers to use in obi go --debug=<debugger>
debuggers:
  gdb: "gdb -ex run --args"
  lldb: "lldb --"
  strace: "sudo strace"
  apitrace: "apitrace trace"
```

And use them like so:
```bash
obi go --debug=gdb roomname
```

When using `--debug` with a remote set of machines, the application is launched in a tmux session with a name matching the target name. This allows one to ssh into one of the machines, attach to the tmux session and poke around:

```bash
obi go --debug=gdb roomname
ssh -t user@host-in-roomname tmux attach -t targetname
```

This assumes that tmux is installed on the remote machines.

#### example

```bash
# Launch the application on the local machine
obi go
# Launch application on the host machines listed under the room named room
obi go room
# Launch the application with lldb
obi go --debug="lldb --"
# Launch the application with apitrace in a remote room
obi go --debug="apitrace trace" room
```

### obi stop [room-name]
---
`obi stop [<room-name>]` stops the application. If `<room-name>` is not specified, then the application is stopped on the local machine.

#### example
```bash
# Stop the application on the local machine
obi stop
# Stop the application on the host machines listed under the room named room
obi stop room
```

### obi build [room-name]
---
`obi build [<room-name>]` builds the application. If `<room-name>` is not specified, then the application is built on the local machine.

#### example
```bash
# Build the application on the local machine
obi build
# Build the application on the host machines listed under the room named room
obi build room
```

### obi clean [room-name]
---
`obi clean [<room-name>]` cleans the build directory. If `<room-name>` is not specified, then the build directory on the local machine is cleaned.

#### example
```bash
# Clean the application build directory on the local machine
obi clean
# Clean the application build directory on the host machines listed under the room named room
obi clean room
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
