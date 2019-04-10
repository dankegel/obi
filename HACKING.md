# Hacking on obi

## Dependencies

    pip install docopt==0.6.2' fabric==1.10.3' jinja2==2.8.1' pyyaml==3.11


## Tips

When developing obi, you may want to test your changes with a real world
project.  Installing it with pip or homebrew every time you make a change can
be tedious.

You can instead use an ["editable"](https://pip.pypa.io/en/latest/reference/pip_install/?highlight=editable#editable-installs) install with `pip`.

```bash
brew unlink obi
pip install --local -e .
obi --help
```

Changes you make in this folder will be reflected when you run `obi` again.
When you're finished developing:

```bash
pip uninstall oblong-obi
brew link obi
```

### ye olde way

Instead, you can add your local obi source tree to `PYTHONPATH` and execute it
with `python -m obi`.  For example:

    cd ~/myawesomeproject
    export PYTHONPATH=$HOME/src/obi:$PYTHONPATH
    python -m obi go orbital-weapons-platform

Will run obi from the source tree at `$HOME/src/obi`.

You may want to also use a [virtualenv][] to keep this project's library
requirements isolated for development.

[virtualenv]: https://virtualenv.pypa.io/en/stable/

## manpage

obi's manpage is generated from `obi.1.txt` which is an asciidoc file. Regenerate
the roff file `obi.1` with asciidoc's `a2x` command:

    a2x --doctype manpage --format manpage obi.1.txt
