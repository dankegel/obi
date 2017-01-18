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
from fabric.api import (local, run) # the global env variable
from fabric.api import (task, parallel, runs_once) #decorators

from fabric.utils import abort
from fabric.contrib.project import rsync_project
from fabric.contrib.files import exists
import fabric.colors

# Courtesy of https://github.com/pyinvoke/invoke/issues/324#issuecomment-215289564
@task
def dryrun():
    """Show, but don't run fabric commands"""

    global local, run
    fabric.state.output['running'] = False

    # Redefine the local and run functions to simply output the command
    def local(command, capture=False, shell=None, running=None):
        print("{}".format(command))

    def run(command, shell=True, pty=True, combine_stderr=None, quiet=False,
            warn_only=False, stdout=None, stderr=None, running=None, timeout=None, shell_escape=None,
            capture_buffer_size=None):
        print("ssh -t {}@{} \"{}\"".format(env.user, env.host_string, command))

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
    env.local_project_dir = os.path.dirname(project_config)
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
        env.project_dir = env.local_project_dir
        env.file_exists = os.path.exists
        env.rsync = lambda: None # Don't rsync when running locally -- noop
        env.cd = fabric.context_managers.lcd
        # Generate a shell script that duplicates the task
        task_name = task_name or env.tasks[-1]
        env.run = local
        env.background_run = env.run
        env.relpath = os.path.relpath
        env.launch_format_str = "{0} {1}"
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
        env.run = run
        env.background_run = lambda cmd: env.run(cmd, pty=False)
        env.file_exists = fabric.contrib.files.exists
        env.rsync = rsync_task
        env.cd = fabric.context_managers.cd
        env.relpath = lambda p: p
        env.launch_format_str = "sh -c '(({0} nohup {1} > {2} 2> {2}) &)'"
        env.debug_launch_format_str = "tmux new -d -s {0} '{1}'".format(env.target_name, "{0} {1} {2}")
    env.build_dir = os.path.abspath(env.relpath(os.path.join(env.project_dir, env.config.get("build-dir", "build"))))

@task
@parallel
def build_task():
    """
    obi build
    """
    with env.cd(env.project_dir):
        user_specified_build = env.config.get("build-cmd", None)
        if env.config.has_key("build-cmd"):
            if user_specified_build:
                env.run(user_specified_build)
        else:
            # Arguments for the cmake step
            cmake_args = env.config.get("cmake-args", [])
            cmake_args = " ".join(cmake_args)
            # Arguments for the build step
            build_args = env.config.get("build-args", [])
            build_args = " ".join(build_args)
            env.run("mkdir -p {0}".format(env.build_dir))
            env.run("cmake -H\"{0}\" -B\"{1}\" {2}".format(env.project_dir, env.build_dir, cmake_args))
            env.run("cmake --build \"{0}\" -- {1}".format(env.build_dir, build_args))

@task
@parallel
def clean_task():
    """
    obi clean
    """
    with env.cd(env.project_dir):
        user_specified_clean = env.config.get("clean-cmd", None)
        if env.config.has_key("clean-cmd"):
            if user_specified_clean:
                env.run(user_specified_clean)
        else:
            clean_cmd = "rm -rf {0} || true".format(env.build_dir)
            env.run(clean_cmd)

@task
@parallel
def stop_task():
    """
    obi stop
    """
    with env.cd(env.project_dir):
        # fall-back to on-stop-cmds for backwards compatibility
        # TODO(jshrake): remove support for the amiguous on-stop-cmds key
        for cmd in env.config.get("pre-stop-cmds", env.config.get("on-stop-cmds", [])):
            env.run(cmd)
    with env.cd(env.project_dir):
        for cmd in env.config.get("local-pre-stop-cmds", []):
            local(cmd)
    default_stop = "pkill -SIGINT -f '[a-z/]+{0} .*' || true".format(env.target_name)
    stop_cmd = env.config.get("stop-cmd", default_stop)
    env.run(stop_cmd)
    with env.cd(env.project_dir):
        for cmd in env.config.get("post-stop-cmds", []):
            env.run(cmd)
    with env.cd(env.project_dir):
        for cmd in env.config.get("local-post-stop-cmds", []):
            local(cmd)

@task
@parallel
def fetch_task(fetch_files_to_dir, files):
    """
    obi fetch
    """
    fetch_dir = fetch_files_to_dir + '/%(host)s/%(path)s'
    files_to_fetch = files or env.config.get("fetch", [])
    with env.cd(env.project_dir):
        for f in files_to_fetch:
            try:
                fabric.operations.get(f, fetch_dir)
            # dont fail when f doesn't exist on the remote machines
            except:
                continue

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
        target, # {0}
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
    """ NOTE(jshrake): local_dir must end in a trailing slash
    From http://docs.fabfile.org/en/1.11/api/contrib/project.html
    - If local_dir ends with a trailing slash, the files will be
    dropped inside of remote_dir.
    E.g. rsync_project("/home/username/project/", "foldername/")
    will drop the contents of foldername inside of /home/username/project.
    - If local_dir does not end with a trailing slash
    (and this includes the default scenario, when local_dir is not
    specified), remote_dir is effectively the "parent" directory, and
    new directory named after local_dir will be created inside of it.
    So rsync_project("/home/username", "foldername") would create
    a new directory /home/username/foldername (if needed) and place the
    files there.
    """
    env.run("mkdir -p {0}".format(env.project_dir))
    return fabric.contrib.project.rsync_project(
        local_dir=env.local_project_dir + "/",
        remote_dir=env.project_dir,
        delete=True,
        exclude=env.config.get("rsync-excludes", []),
        extra_opts=env.config.get("rsync-extra-opts", "--copy-links --partial"),
        capture=True)

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
