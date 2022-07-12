==================
os2borgerpc-client
==================

|pipeline status|
|coverage report|

.. |pipeline status| image:: https://git.magenta.dk/os2borgerpc/os2borgerpc-client/badges/development/pipeline.svg
.. |coverage report| image:: https://git.magenta.dk/os2borgerpc/os2borgerpc-client/badges/development/coverage.svg

This repository contains os2borgerpc-client, a Python library which functions as a
client for the OS2borgerPC Admin system.

The code was created by Magenta ApS (http://www.magenta-aps.dk) and is part of the
OS2borgerPC project. For more info about the OS2borgerPC project, please see the 
official home page:

    https://os2.eu/produkt/os2borgerpc

and the offical Github project:

    https://github.com/OS2borgerPC/

Read the documentation for this project in docs/ or at 
`Read The Docs <https://os2borgerpc-client.readthedocs.io/>`_.

This library is available to you according to the conditions in version 3 of
the GNU General Public License. See the LICENSE file for details.

Files
=====

+----------------------------------------+-------------------------------------------------------------------------------------------------+
| Program                                | Description                                                                                     |
+----------------------------------------+-------------------------------------------------------------------------------------------------+
| bin/admin_connect.sh                   | Used to connect arbitrary Debian distros to the admin site. Not currently maintained.           |
| bin/get_os2borgerpc_config             | Gets a config value from os2borgerpc.conf, via config.py                                        |
| bin/jobmanager                         | A symlink to os2borgerpc/client/jobmanager.py                                                   |
| bin/os2borgerpc_find_gateway           | Used to connect to OS2borgerPC-admin via a gateway. Not currently maintained                    |
| bin/os2borgerpc_push_config_keys       | Pushes the local configs in /etc/os2borgerpc/os2borgerpc.conf to the adminsite                  |
| bin/os2borgerpc_register_in_admin      | Registers the machine with the adminsite. Required before jobmanager works.                     |
| bin/randomize_jobmanager.sh            | Randomizes the interval and start time of jobmanager, for performance reasons                   |
| bin/register_new_os2borgerpc_client.sh | Interactively gathers information about the machine and then runs os2borgerpc_register_in_admin |
| bin/set_os2borgerpc_config             | Sets a config value in os2borgerpc.conf, via config.py                                          |
+----------------------------------------+-------------------------------------------------------------------------------------------------+
| os2borgerpc/client/security            | The OS2borgerPC client security system, executes security scripts and reports back              |
| os2borgerpc/client/admin_client.py     | The interface between the client and the adminsite. Communicates with rpc.py on the admin site  |
| os2borgerpc/client/config.py           | An interface between the client and os2borgerpc.conf                                            |
| os2borgerpc/client/gateway.py          | Used to connect to OS2borgerPC-admin via a gateway. Not currently maintained.                   |
| os2borgerpc/client/jobmanager.py       | Main program of the client: Checks in with the adminsite, run scripts, security scripts etc.    |
| os2borgerpc/client/proxy_setup.py      | Used to connect to OS2borgerPC-admin via a gateway. Not currently maintained.                   |
| os2borgerpc/client/utils.py            | Utility scripts for the client                                                                  |
+----------------------------------------+-------------------------------------------------------------------------------------------------+
