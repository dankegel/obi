# Hacking on obi

## Tips

When developing obi, you may want to test your changes with a real world
project.  Installing it with pip or homebrew every time you make a change can
be tedious.

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
