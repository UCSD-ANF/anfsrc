#!/bin/bash
# xvfbwrap
#
# Within the Antelope/ANF environment, Call a process that needs an X11
# display to function, firing up a file-based display beforehand,
# killing that display afterward.

MIN_X=1  # per ANF Puppet setup
MAX_X=49 # per ANF Puppet setup
XVFB=$ANTELOPE/bin/Xvfb
test -x $XVFB || exit 1

# Hunt around for a DISPLAY to use.
i=$MIN_X
while [ $MAX_X -ge $i ]; do
    $XVFB :$i -fbdir /var/tmp -screen 0 1920x1200x24 2>/dev/null &
    mypid=$!
    sleep 1

    if [ -e /tmp/.X11-unix/X${i} ]; then
        export DISPLAY=":${i}"
        break
    fi
    let i++
done
eval "$@"
retval=$?
kill -s SIGTERM $mypid >/dev/null
wait $mypid
exit $retval
