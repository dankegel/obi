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
    project_config = project_yaml()
    config = load_project_config(project_config)

    # Abort if no project name found
    project_name = config.get("name", None)
    if not project_name:
        abort("No name key found in the project.yaml. Please specify a project name")
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

    # Calling basename on project_name should be harmless
    # In the case that the user specified target, say, build/foo,
    # then basename gives us foo
    env.target_name = os.path.basename(
        env.config.get("target", env.project_name))

    # Running locally if:
    # - User specified is-local: True
    # - Room name is localhost
    # - Hosts is empty
    if room.get("is-local", room_name == "localhost" or not room.get("hosts", [])):
        env.hosts = ['localhost']
        env.use_ssh_config = False
        env.project_dir = os.path.dirname(project_config)
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
            print("# brew tap Oblong/homebrew-tools", file=f)
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
            with open(task_sh_file, 'a') as f:
                print(cmd, file=f)
            # Gracefully handle keyboard interrupts
            try:
                fabric.api.local(cmd)
            except KeyboardInterrupt:
                pass
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
        env.launch_format_str = "{0} {1} 2>&1 | tee -a {2}"
        env.debug_launch_format_str = "{0} {1} {2}"
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
        env.launch_format_str = "sh -c '(({0} nohup {1} > {2} 2> {2}) &)'"
        env.debug_launch_format_str = "tmux new -d -s {0} '{1}'".format(env.target_name, "{0} {1} {2}")
    env.build_dir = env.relpath(
        os.path.join(env.project_dir,
                     env.config.get("build-dir", "build")))

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
        env.run("cmake -H{0} -B{1} {2}".format(env.project_dir, env.build_dir, cmake_args))
        env.run("cmake --build {0} -- {1}".format(env.build_dir, build_args))

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
    default_stop = "pkill -KILL -f '[a-z/]+{0} .*' || true".format(env.target_name)
    stop_cmd = env.config.get("stop-cmd", default_stop)
    env.run(stop_cmd)

@task
@parallel
def launch_task(debugger, extras):
    """
    Handles launching the application in obi go
    """

    target = ""
    # Did the user specify a target?
    config_target = env.config.get("target", None)
    if config_target:
        target = os.path.join(env.project_dir, config_target)
    # TODO(jshrake): Consider nesting these conditionals
    # Look for a binary with name env.target_name in the build directory
    if not env.file_exists(target):
        target = os.path.join(env.build_dir, env.target_name)
    # Look for a binary with name env.target_name in the binary directory
    if not env.file_exists(target):
        target = os.path.join(env.project_dir, "bin", env.target_name)
    # Just give up -- can't find the target name
    if not env.file_exists(target):
        abort("Cannot find target binary to launch. Please specify the relative path to the binary via the target key")

    launch_args = env.config.get("launch-args", [])

    formatted_launch = "{0} {1} {2}".format(
        env.relpath(target), # {0}
        " ".join(extras), # {1}
        " ".join(launch_args) # {2}
    )

    env_vars = env.config.get("env-vars", {})
    env_vars = " ".join(["{0}={1}".format(key, val) for key, val in env_vars.items()])

    with env.cd(env.project_dir):
        # Process pre-launch commands
        for cmd in env.config.get("pre-launch-cmds", []):
            env.run(cmd)
        if debugger:
            debug_cmd = debugger
            debuggers = env.config.get("debuggers", None)
            if debuggers:
                debug_cmd = debuggers.get(debugger, debug_cmd)
            default_launch = env.debug_launch_format_str.format(env_vars, debug_cmd, formatted_launch)
            launch_cmd = env.config.get("debug-launch-cmd", default_launch)
            env.background_run(launch_cmd)
        else:
            log_file = env.relpath(os.path.join(env.project_dir, env.target_name + ".log"))
            default_launch = env.launch_format_str.format(env_vars, formatted_launch, log_file)
            launch_cmd = env.config.get("launch-cmd", default_launch)
            env.background_run(launch_cmd)
        # Process the post-launch commands
        for cmd in env.config.get("post-launch-cmds", []):
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

def load_project_config(config_path):
    """
    Returns a Dict of the project.yaml specifed by config_path or aborts on
    failure
    """
    try:
        with open(config_path) as config_file:
            config = yaml.load(config_file)
            if not config:
                abort("Error: problem loading " + project_config_file)
            return config
    except Exception as e:
        abort("Cannot load project.yaml file at {0}\nException: {1}".format(config_path, e.message))

def project_yaml():
    """
    Returns the absolute path to the project.yaml file
    This function will search the current working directory on up to root
    If no project.yaml file is found, aborts
    """
    current = os.getcwd()
    parent = parent_dir(current)
    while current != parent:
        test_file = os.path.join(current, "project.yaml")
        if os.path.exists(test_file):
            return os.path.abspath(test_file)
        else:
            current = parent
            parent = parent_dir(current)
    abort("Could not find the project.yaml file in {0} or any parent directories".format(os.getcwd()))
