Version 2.5.0, April 09, 2024
-----------------------------

New in this version:

- Support new integration with Quria used for login via Quria credentials
  with or without booking
- Update functions related to SMSTeknik integration to support new functionality
- Report kernel version and last update time during every check-in
- Prevent PC info configurations from becoming too long
- Hide password input parameters everywhere in script log output
- Keep tabs in log output
- Add readthedocs.yaml

Version 2.4.1, December 20, 2023
--------------------------------

New in this version:

- Report the computer manufacturer, CPU and RAM to the admin-site during registration

Version 2.4.0, November 28, 2023
--------------------------------

New in this version:

- Support new integration with SMSTeknik and Easy!Appointments used for login
  via sms verification with or without booking

Version 2.3.1, November 9, 2023
-------------------------------

New in this version:

- Make the client report the current IP addresses to the admin-site during check-in
- Report the computer model to the admin-site during registration
- Randomize check-in times on seconds during registration
- Support new Cicero functionality that prevents simultaneous logins
- Remove outdated and unused Gateway functionality

Version 2.2.1, May 23, 2023
---------------------------

New in this version:

- Translate client user interaction to English

Version 2.2.0, February 16, 2023
--------------------------------

New in this version:

- Make the update process be dependent on much less code, so it's likelihood of breaking is reduced
- Halve the release/updating speed in case errors are discovered
- Add commented out code for easily installing from testpypi instead

Version 2.1.1, February 16, 2023
--------------------------------

New in this version:

- Make the client support any distribution without printing an error
  (mainly to prepare for supporting 22.04 ).
- Make push_config_keys print out an error when receiving zero arguments and explain why.
- Black got new formatting rules. Apply them.

Version 2.1.0, September 15, 2022
---------------------------------

New in this version:

- Fix a bug so logs in non-UTF-8 character sets are handled in some fashion.
  Especially latin-1.
- Run pending jobs before dealing with unsent jobs, so if unsent jobs cause
  jobmanager to crash, it can still be solved by running new scripts.
- If check-in with the adminsite fails continue to run anyway.

Version 2.0.1, August 22, 2022
------------------------------

New in this version:

- Fix a bug so control characters in log_output which cause xmlrpc to fail are
  filtered out before sending them to the server.

Version 2.0.0, July 11, 2022
----------------------------

New in this version:

- Build auto-updating itself into the client.
- Refactor security system and separate it out into its own file.
- Consolidate calls to send_config_keys.
- Security system changed to use a resolution down to seconds rather than just
  minutes.
- Add automated tests.
- Remove parameters.json after script run, sanitize log output.
- Improved documentation.
- Allow uppercase in computer names again.
- Set /etc/hosts correctly.
- Add linting.


Version 1.3.0, February 14, 2022
---------------------------------

New in this version:

- Ensure job status never goes unreported.
- Checkin times now randomized when PC is registered with the admin
  system.


Version 1.2.0, November 24, 2021
--------------------------------

New in this version:

- Documentation now on Read The Docs, reference to this documentation in
  README.
- Ensure user enters a valid name for the newly registered PC.
- New RPC endpoint (citizen_login) added to client to support integration with
  existing library login systems such as Cicero.


Version 1.1.3, May 7, 2021
-------------------------------

New in this version:

- Display Ubuntu version in computer's configuration.
- Fix ValueError/conversion error from YAML.
- Improved documentation.


Version 1.1.2, January 29, 2021
-------------------------------

New in this version:

- Fix bug in handling of basenames for downloaded files.


Version 1.1.1, January 29, 2021
-------------------------------

New in this version:

- Fix unsafe deletion of old security scripts.


Version 1.1.0, January 13, 2021
-------------------------------

New in this version:

- Proper handling of timeout and version.


Version 1.0.1, January 5, 2021
------------------------------

New in this version:

- The OS2borgerPC client was moved to its own repository.
