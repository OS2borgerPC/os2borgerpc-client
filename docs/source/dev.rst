Technical Documentation
=======================

Files
-----

======================================== ==================================================================================================
 Program                                  Description
======================================== ==================================================================================================
 bin/admin_connect.sh                     Used to connect arbitrary Debian distros to the admin site. Not currently maintained
 bin/get_os2borgerpc_config               Gets a config value from os2borgerpc.conf, via config.py
 bin/jobmanager                           A symlink to os2borgerpc/client/jobmanager.py
 bin/os2borgerpc_push_config_keys         Pushes the local configs in /etc/os2borgerpc/os2borgerpc.conf to the adminsite
 bin/os2borgerpc_register_in_admin        Registers the machine with the adminsite. Required before jobmanager works
 bin/randomize_jobmanager.sh              Randomizes the interval and start time of jobmanager, for performance reasons
 bin/register_new_os2borgerpc_client.sh   Interactively gathers information about the machine and then runs os2borgerpc_register_in_admin
 bin/set_os2borgerpc_config               Sets a config value in os2borgerpc.conf, via config.py

 os2borgerpc/client/security              The OS2borgerPC client security system, executes security scripts and reports back
 os2borgerpc/client/admin_client.py       The interface between the client and the adminsite. Communicates with rpc.py on the admin site
 os2borgerpc/client/config.py             An interface between the client and os2borgerpc.conf
 os2borgerpc/client/jobmanager.py         Main program of the client: Checks in with the adminsite, run scripts, security scripts etc.
 os2borgerpc/client/utils.py              Utility scripts for the client
======================================== ==================================================================================================
