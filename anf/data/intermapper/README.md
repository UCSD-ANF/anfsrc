Intermapper Probes
------------------

This directory contains intermapper probes for Antelope. They are thin wrappers
for the various Nagios plugins in the antelope\_contrib tree.

To install them, either copy them to the Intermapper directory under Probes and
restart Intermapper, or load them in via the GUI client.

Note that they require a symlink in /opt/antelope/current-version pointing to
the preferred version of Antelope for Intermapper checks. As such, they are not
really ready for inclusion in antelope\_contrib proper
