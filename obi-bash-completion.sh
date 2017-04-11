
_obi()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -eq 1 ]; then
        COMPREPLY=( $( compgen -W '-h --help --version rsync template stop build clean go new fetch' -- $cur) )
    else
        case ${COMP_WORDS[1]} in
            rsync)
            _obi_rsync
        ;;
            template)
            _obi_template
        ;;
            stop)
            _obi_stop
        ;;
            build)
            _obi_build
        ;;
            clean)
            _obi_clean
        ;;
            go)
            _obi_go
        ;;
            new)
            _obi_new
        ;;
            fetch)
            _obi_fetch
        ;;
        esac

    fi
}

_obi_template()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -eq 2 ]; then
        COMPREPLY=( $( compgen -W ' upgrade list remove install' -- $cur) )
    else
        case ${COMP_WORDS[2]} in
            upgrade)
            _obi_template_upgrade
        ;;
            list)
            _obi_template_list
        ;;
            remove)
            _obi_template_remove
        ;;
            install)
            _obi_template_install
        ;;
        esac

    fi
}

_obi_template_upgrade()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -ge 3 ]; then
        COMPREPLY=( $( compgen -W '--template_home= ' -- $cur) )
    fi
}

_obi_template_list()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -ge 3 ]; then
        COMPREPLY=( $( compgen -W '--template_home= ' -- $cur) )
    fi
}

_obi_template_remove()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -ge 3 ]; then
        COMPREPLY=( $( compgen -W '--template_home= ' -- $cur) )
    fi
}

_obi_template_install()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -ge 3 ]; then
        COMPREPLY=( $( compgen -W '--template_home= ' -- $cur) )
    fi
}

_obi_stop()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -eq 2 ]; then
        COMPREPLY=( $( compgen -W "$(_obi_roomnames) --dry-run " -- $cur) )
    fi
    if [ $COMP_CWORD -gt 2 ]; then
      COMPREPLY=( $( compgen -W '--dry-run --' -- $cur) )
    fi
}

_obi_rsync()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -eq 2 ]; then
        COMPREPLY=( $( compgen -W "$(_obi_roomnames) --dry-run " -- $cur) )
    fi
    if [ $COMP_CWORD -gt 2 ]; then
      COMPREPLY=( $( compgen -W '--dry-run --' -- $cur) )
    fi
}

_obi_build()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -eq 2 ]; then
        COMPREPLY=( $( compgen -W "$(_obi_roomnames) --dry-run " -- $cur) )
    fi
    if [ $COMP_CWORD -gt 2 ]; then
      COMPREPLY=( $( compgen -W '--dry-run --' -- $cur) )
    fi
}

_obi_clean()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -eq 2 ]; then
        COMPREPLY=( $( compgen -W "$(_obi_roomnames) --dry-run " -- $cur) )
    fi
    if [ $COMP_CWORD -gt 2 ]; then
      COMPREPLY=( $( compgen -W '--dry-run --' -- $cur) )
    fi
}

_obi_go()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -eq 2 ]; then
        COMPREPLY=( $( compgen -W "$(_obi_roomnames) --debug= --dry-run --" -- $cur) )
    fi
    if [ $COMP_CWORD -gt 2 ]; then
      COMPREPLY=( $( compgen -W '--debug= --dry-run --' -- $cur) )
    fi
}

_obi_new()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -eq 2 ]; then
      COMPREPLY=( $( compgen -W "$(_obi_installed_templates)" -- $cur) )
    fi
    if [ $COMP_CWORD -ge 3 ]; then
        COMPREPLY=( $( compgen -W '--template_home= --g_speak_home= ' -- $cur) )
    fi
}

_obi_fetch()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -eq 2 ]; then
        COMPREPLY=( $( compgen -W "$(_obi_roomnames) --dry-run " -- $cur) )
    fi
    if [ $COMP_CWORD -gt 2 ]; then
      COMPREPLY=( $( compgen -W '--dry-run --' -- $cur) )
    fi
}

_obi_installed_templates ()
{
  echo $(obi template list | tail -n +2)
}

_obi_roomnames()
{
  python - <<EOF
import os
import yaml
def parent_dir(current_dir):
    return os.path.abspath(os.path.join(current_dir, os.pardir))

def load_project_config(config_path):
    try:
        with open(config_path) as config_file:
            config = yaml.load(config_file)
            if not config:
                abort("Error: problem loading " + project_config_file)
            return config
    except Exception as e:
        abort("Cannot load project.yaml file at {0}\nException: {1}".format(config_path, e))

def project_yaml():
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

projectyaml = load_project_config(project_yaml())
for k in sorted(projectyaml['rooms'].keys()) :
  print k
EOF
}

complete -F _obi obi
