#!/usr/bin/env python
"""
obi is a command-line tool for working with gspeak projects.

Available tasks:

build             Builds the project (optionally, on numerous machines)
clean             Clean the build directory (optionally, on numerous machines)
go                Build, stop, and run the project (optionally, on numerous machines)
new               Generate project scaffolding based on a obi template
stop              Stops the application (optionally, on numerous machines)
rsync             Rsync your local project directory to remote machines
fetch             Download remote files to your local project directory
script            Run a local script on remote machines
ls                List obi templates
template install  Install an obi template
template remove   Remove an installed obi template
template upgrade  Upgrade an installed obi template

Edit project.yaml (in your project folder) to configure sets of machines for
go/stop, set arguments for building and launching the program, choose feld &
screen proteins, and set the names of pools that your program will use.

Usage:
  obi new <template> <name> [--template_home=<path>] [--g_speak_home=<path>]
  obi go [<room>] [--debug=<debugger>] [--dry-run] [--] [<extras>...]
  obi stop [<room>] [--dry-run]
  obi clean [<room>] [--dry-run]
  obi build [<room>] [--dry-run]
  obi rsync <room> [--dry-run]
  obi fetch <room> [<file>...] [--dry-run]
  obi script <room> <script> [--dry-run]
  obi ls [--template_home=<path>]
  obi template install <giturl> [<name>] [--template_home=<path>]
  obi template remove <name> [--template_home=<path>]
  obi template upgrade <name> [--template_home=<path>]
  obi -h | --help | --version

Options:
  -h --help               Show this screen.
  --version               Show version.
  --dry-run               Optional: output the list of commands that the task runs.
  --g_speak_home=<path>   Optional: absolute path of g-speak dir to build against.
  --template_home=<path>  Optional: path containing installed obi templates.
  --debug=<debugger>      Optional: launches the application in a debugger.
"""

from __future__ import print_function
import os
import re
import sys
import pkg_resources
import imp
import subprocess
import errno
import fabric
import docopt
import datetime
from . import task

def mkdir_p(path):
    """
    mkdir -p
    http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
    """
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

def get_g_speak_home(arguments):
    """
    Extract the gspeak version by hook or by crook
    We'll examine the gspeak argument passed, the G_SPEAK_HOME
    enviornment variable, and finally we'll even look at your
    files for /opt/oblong/g-speakX.YY
    """
    g_speak_home = ""
    set_by = None
    if arguments["--g_speak_home"]:
        g_speak_home = arguments["--g_speak_home"]
        set_by = "command-line"
    elif 'G_SPEAK_HOME' in os.environ:
        # extract the version from the enviornment variable
        g_speak_home = os.environ['G_SPEAK_HOME']
        set_by = "environment variable G_SPEAK_HOME"
    else:
        path = os.path.join(os.path.sep, "opt", "oblong")
        try:
            items = [os.path.join(path, item) for item in os.listdir(path) if "g-speak" in item]
            items = [item for item in items if os.path.isdir(item)]
            items.sort()
            # the last element will be the directory with the most recent
            # version of g-speak
            g_speak_home = items[-1]
            set_by = "directory lookup"
        except (OSError, IndexError):
            print("Could not find the g_speak home directory in {}"
                  .format(path))
            print("Run new again and specify: --g_speak_home=/path/to/g-speak")
            sys.exit(1)

    print("Found {0} by {1}".format(g_speak_home, set_by))
    if not (os.path.exists(g_speak_home) and os.path.isdir(g_speak_home)):
        print("{0} does not exist or is not a directory.".format(g_speak_home))
        sys.exit(1)
    return g_speak_home


def main():
    """
    the entry_point for obi
    """
    version = pkg_resources.require("oblong-obi")[0].version

    # easter egg
    if sys.argv[1:] == ["wan"]:
        return subprocess.call(["telnet", "towel.blinkenlights.nl"])

    # defaults for the template subcommands
    default_base_template_dir = os.path.join(os.path.expanduser("~"), ".local/share")
    default_obi_template_dir = os.path.join(
        os.environ.get("XDG_DATA_HOME", default_base_template_dir), "oblong", "obi")

    arguments = docopt.docopt(__doc__, version=version, help=True)
    room = arguments.get("<room>", "localhost") or "localhost"
    if room == '--':
        room = "localhost" # special case: docopt caught '--' as a room name

    if arguments.get('--dry-run', False):
        fabric.api.execute(task.dryrun)
    if arguments['new']:
        template_root = arguments["--template_home"] or default_obi_template_dir
        project_name = arguments['<name>']
        template_name = arguments['<template>']
        template_path = os.path.join(template_root, template_name, template_name + ".py")
        if not os.path.exists(template_path):
            print("Could not find template {0}".format(template_name))
            print("Expected to find {0}".format(template_path))
            print("Installed templates:\n{0}".format(
                "\n".join([d for d in os.listdir(template_root)])))
            return 1
        template = imp.load_source(template_name, template_path)
        if not hasattr(template, 'obi_new'):
            print ("Error: template {0} does not expose a funciton named obi_new".format(template_name))
            return 1
        project_path = os.path.join(os.getcwd(), project_name)
        g_speak_home = get_g_speak_home(arguments)
        # regex to extract g-speak version number
        # if g_speak_home = "/opt/oblong/g-speak3.19"
        # then g_speak_vers = "3.19"
        g_speak_version = re.search(r'(\d+\.\d+)', g_speak_home).group()
        template.obi_new(project_path=project_path,
                         project_name=project_name,
                         g_speak_home=g_speak_home,
                         g_speak_version=g_speak_version)
        print("Project {0} created successfully!".format(arguments['<name>']))
    elif arguments['build']:
        res = fabric.api.execute(task.room_task, room, "build")
        res.update(fabric.api.execute(fabric.api.env.rsync))
        res.update(fabric.api.execute(task.build_task))
    elif arguments['go']:
        extras = arguments.get('<extras>', [])
        # Gracefully handle keyboard interrupts
        try:
            res = fabric.api.execute(task.room_task, room, "go")
            res.update(fabric.api.execute(fabric.api.env.rsync))
            res.update(fabric.api.execute(task.build_task))
            res.update(fabric.api.execute(task.stop_task))
            res.update(fabric.api.execute(task.launch_task, arguments['--debug'], extras))
        except KeyboardInterrupt:
            pass
    elif arguments['stop']:
        res = fabric.api.execute(task.room_task, room, "stop")
        res.update(fabric.api.execute(task.stop_task))
    elif arguments['clean']:
        res = fabric.api.execute(task.room_task, room, "clean")
        res.update(fabric.api.execute(task.clean_task))
    elif arguments['rsync']:
        res = fabric.api.execute(task.room_task, room, "rsync")
        res.update(fabric.api.execute(fabric.api.env.rsync))
    elif arguments['fetch']:
        timestr = datetime.datetime.now().strftime("%Y%m%d.%H%M%S")
        fetch_dir = "fetched.{}".format(timestr)
        files = arguments.get('<file>', [])
        res = fabric.api.execute(task.room_task, room, "fetch")
        res.update(fabric.api.execute(task.stop_task))
        res.update(fabric.api.execute(task.fetch_task, fetch_dir, files))
        # Try to store git info
        try:
            git_diff = subprocess.check_output(["git", "diff", "HEAD"])
            with open(os.path.join(fetch_dir, "git.diff"), "w") as git_diff_file:
                git_diff_file.write(git_diff)
        except:
            pass
        try:
            git_log = subprocess.check_output(["git", "log"])
            with open(os.path.join(fetch_dir, "git.log"), "w") as git_log_file:
                git_log_file.write(git_log)
        except:
            pass
    elif arguments['script']:
        res = fabric.api.execute(task.room_task, room, "script")
        res.update(fabric.api.execute(task.script_task, arguments.get('<script>', "")))


    elif arguments['ls']:
        template_root = arguments["--template_home"] or default_obi_template_dir
        if os.path.exists(template_root):
            print("Installed templates:\n{0}".format(
                "\n".join([d for d in os.listdir(template_root)])))
        else:
            print("No templates installed at " + template_root)
    elif arguments['template']:
        if arguments['install']:
            template_root = arguments["--template_home"] or default_obi_template_dir
            mkdir_p(template_root)
            giturl = arguments['<giturl>']
            name = arguments['<name>'] or os.path.basename(giturl)
            res = subprocess.call(["git", "clone", giturl, name], cwd=template_root)
            print("Installed template {} to {}".format(name, template_root))
            return res
        elif arguments['upgrade']:
            template_root = arguments["--template_home"] or default_obi_template_dir
            template_name = arguments["<name>"]
            template_path = os.path.join(template_root, template_name)
            if os.path.exists(template_path):
                res = subprocess.call(["git", "pull"], cwd=template_path)
                print("Upgraded template at {}".format(template_path))
                return res
            else:
                print("No template installed with name " + template_name)
                return 1
        elif arguments['remove']:
            template_root = arguments["--template_home"] or default_obi_template_dir
            template_name = arguments["<name>"]
            template_path = os.path.join(template_root, template_name)
            if os.path.exists(template_path):
                return subprocess.call(["rm", "-rf", template_path])
            else:
                print("No template installed with name " + template_name)
                return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
