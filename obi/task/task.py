'''
Implementations for the obi tasks
- obi clean
- obi stop
- obi build
- obi go
'''
from __future__ import print_function
import fabric
import os
import stat
import yaml

from fabric.api import env  # the global env variable
from fabric.api import (task, parallel, runs_once) #decorators
from fabric.utils import abort
from fabric.contrib.project import rsync_project
from fabric.contrib.files import exists
import fabric.colors

@task
@runs_once
def room_task(room_name, task_name=None):
    """
    Configures the fabric globabl env variable for other tasks
    """
    # Load the project.yaml file so we can extract configuration for the given room_name
    project_yaml = os.path.join(project_yaml_wd(), "project.yaml")
    if not os.path.exists(project_yaml):
        abort("Could not find a project.yaml file in this directory or any above it!")
    config = None
    with open(project_yaml) as data_file:
        config = yaml.load(data_file)
    if not config:
        abort("Error: problem loading " + project_yaml)
    # Abort if no project name found
    project_name = config.get("name", None)
    if not project_name:
        abort("Could not find a name listed in project.yaml")
    env.project_name = project_name
    # Abort if we cannot find room_name in rooms
    rooms = config.get("rooms", {})
    room = rooms.get(room_name, None)
    if not room:
        abort("""{0} is not a room name listed in project.yaml\n
              Available room names: {1}""".format(room_name, rooms.keys()))

    # Extract the top-level config sans the rooms config
    config_no_rooms = config.copy()
    config_no_rooms.pop("rooms", None)
    # Merge the config of our room into the top-level
    env.config = config_no_rooms
    env.config.update(room)

    # Running locally if:
    # - User specified is-local: True
    # - Room name is localhost
    # - Hosts is empty
    if room.get("is-local", room_name == "localhost" or not room.get("hosts", [])):
        env.hosts = ['localhost']
        env.use_ssh_config = False
        env.project_dir = project_yaml_wd()
        env.file_exists = os.path.exists
        env.rsync = lambda: None # Don't rsync when running locally -- noop
        env.cd = fabric.context_managers.lcd
        # Generate a shell script that duplicates the task
        task_name = task_name or env.tasks[-1]
        task_sh_name = "obi-{0}-{1}.sh".format(task_name.replace(":", ""), room_name)
        task_sh_file = os.path.join(env.project_dir, task_sh_name)
        with open(task_sh_file, 'w') as f:
            print("#!/usr/bin/env bash", file=f)
            print("# Produced with obi!", file=f)
            print("# brew tap solutions/tools git@gitlab.oblong.com:solutions/homebrew-tools", file=f)
            print("# brew install obi", file=f)
            print("set -e", file=f)
            print("set -v\n", file=f)
        # Make sure the script is executable
        task_sh_st = os.stat(task_sh_file)
        os.chmod(task_sh_file, task_sh_st.st_mode | stat.S_IEXEC)
        def local_run(cmd):
            """
            Runs the command locally
            Side effect: write the command to a shell script
            """
            fabric.api.local(cmd)
            with open(task_sh_file, 'a') as f:
                print(cmd, file=f)
        env.run = local_run
        env.background_run = env.run
        def print_shell_script():
            """
            Prints the commands written to the shell script
            See local_run
            """
            print(fabric.colors.magenta("$ cat " + task_sh_file, bold=True))
            with open(task_sh_file, 'r') as f:
                for cmd in f.readlines():
                    print(fabric.colors.green(cmd.rstrip(), bold=True))
        env.print_cmds = print_shell_script
        env.relpath = os.path.relpath
    else:
        env.user = room.get("user", env.local_user) # needed for remote run
        env.hosts = room.get("hosts", [])
        env.use_ssh_config = True
        # Default remote project dir is /tmp/localusername/projectname
        env.project_dir = room.get("project-dir",
                                   os.path.join(os.path.sep,
                                                "tmp",
                                                env.local_user,
                                                project_name))
        env.run = fabric.api.run
        env.background_run = lambda cmd: env.run(cmd, pty=False)
        env.file_exists = fabric.contrib.files.exists
        env.rsync = rsync_task
        env.cd = fabric.context_managers.cd
        env.print_cmds = lambda: None
        env.relpath = lambda p: p
    env.build_dir = env.relpath(
        os.path.join(env.project_dir,
                     env.config.get("build-dir", "build")))
    # Calling basename on project_name should be harmless
    # In the case that the user specified target, say, build/foo,
    # then basename gives us foo
    env.target_name = os.path.basename(
        env.config.get("target", env.project_name))

@task
@parallel
def build_task():
    """
    obi build
    """
    user_specified_build = env.config.get("build-cmd", None)
    if user_specified_build:
        env.run(user_specified_build)
    else:
        # Arguments for the cmake step
        cmake_args = env.config.get("cmake-args", [])
        cmake_args = " ".join(cmake_args)
        # Arguments for the build step
        build_args = env.config.get("build-args", [])
        build_args = " ".join(build_args)
        # Ensure the directory exists
        env.run("mkdir -p {0}".format(env.build_dir))
        env.run("(cd {0}; cmake {1} ..)".format(env.build_dir, cmake_args))
        env.run("(cd {0}; cmake --build . -- {1})".format(env.build_dir, build_args))

@task
@parallel
def clean_task():
    """
    obi clean
    """
    default_clean = "rm -rf {0} || true".format(env.build_dir)
    clean_cmd = env.config.get("clean-cmd", default_clean)
    env.run(clean_cmd)

@task
@parallel
def stop_task():
    """
    obi stop
    """
    with env.cd(env.project_dir):
        for cmd in env.config.get("on-stop-cmds", []):
            env.run(cmd)
    default_stop = "pkill {0} || true".format(env.target_name)
    stop_cmd = env.config.get("stop-cmd", default_stop)
    env.run(stop_cmd)

@task
@parallel
def launch_task(extras):
    """
    Handles launching the application in obi go
    """
    # Format the env variables
    env_vars = env.config.get("env-vars", {})
    env_vars = " ".join(["{0}={1}".format(key, val) for key, val in env_vars.items()])

    # Format the pool names
    pools = env.config.get("pools", {}) or {}
    pools = " ".join(["--{0}={1}".format(name, addr) for name, addr in pools.items()])

    # Configure the room protein flag
    room_protein = env.config.get("room-protein", None)
    room_option = ""
    if room_protein:
        room_option = "--room={0}".format(room_protein)

    # Search for the screen protein
    screen_protein = env.config.get("screen-protein", None)
    if not screen_protein:
        abort("Screen protein not found, specify screen-protein in project.yaml")

    # Search for the feld protein
    feld_protein = env.config.get("feld-protein", None)
    if not feld_protein:
        abort("Feld protein not found, specify feld-protein in project.yaml")

    # Handles launch arguments
    launch_args = env.config.get("launch-args", [])

    # Search for the target in a couple of locations
    target = os.path.join(env.project_dir, env.config.get("target", env.project_name))
    if not env.file_exists(target):
        target = os.path.join(env.build_dir, env.project_name)
    if not env.file_exists(target):
        target = os.path.join(env.project_dir, "bin", env.project_name)
    if not env.file_exists(target):
        abort("""Cannot find target -- please specify the relative path
              to your resulting binary via the target key""")

    formatted_launch = "{0} {1} {2} {3} {4} {5} {6}".format(
        env.relpath(target), # {0}
        pools, # {1}
        " ".join(launch_args), # {2}
        " ".join(extras), # {3}
        room_option, # {4}
        screen_protein, # {5}
        feld_protein) # {6}

    with env.cd(env.project_dir):
        # Process pre-launch commands
        for cmd in env.config.get("pre-launch-cmds", []):
            env.run(cmd)
        # Launch the application in the background
        log_file = env.relpath(os.path.join(env.project_dir, env.project_name + ".log"))
        default_launch = "sh -c '(({0} nohup {1} > {2} 2> {2}) &)'".format(
            env_vars, formatted_launch, log_file)
        env.background_run(env.config.get("launch-cmd", default_launch))
        # Process the post-launch commands
        for cmd in env.config.get("post-lauch-cmds", []):
            env.run(cmd)

@task
@parallel
def rsync_task():
    """
    Task wrapper around fabric's rsync_project
    """
    fabric.api.local(env.config.get("pre-rsync-cmd", ""))
    return fabric.contrib.project.rsync_project(
        remote_dir=parent_dir(env.project_dir),
        delete=True,
        exclude=env.config.get("rsync-excludes", []))

def parent_dir(current_dir):
    """
    Returns the absolute path to the parent directory of current_dir
    """
    return os.path.abspath(os.path.join(current_dir, os.pardir))

def project_yaml_wd():
    """
    Returns the absolute path to the directory containing the project.yaml file
    This function will search the current working directory on up to root
    If no project.yaml file is found, returns None
    """
    current = os.getcwd()
    parent = parent_dir(current)
    while current != parent:
        if os.path.exists(os.path.join(current, "project.yaml")):
            return os.path.abspath(current)
        else:
            current = parent
            parent = parent_dir(current)
    return None