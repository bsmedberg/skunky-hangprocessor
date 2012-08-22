The skunky-hangprocessor project is a temporary solution for processing Firefox
hang reports until Socorro grows the necessary collection/query features. See
https://wiki.mozilla.org/Socorro/Hang_Processing_Proposal for the long-term 
proposal and motivation. See [Mozilla bug 784106](https://bugzilla.mozilla.org/show_bug.cgi?id=784106)
for deployment information.

This app is designed to handle low report volumes (1500 reports/day) and is
not intended to be scalable. That's what Socorro is for.

Typically the collector runs continuously (either directly from the command
line or as a WSGI app using fastcgi or mod_wsgi). A single instance of the
processor also runs on a cron job. The reporting is all flat files that can
be served directly. All data analysis will be done with some combination of
python and pig.

To get more information or help, please contact Benjamin Smedberg <benjamin@smedbergs.us>.
