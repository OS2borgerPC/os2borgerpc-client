Version 2.6.5, March 7, 2025
----------------------------

- Use free -h to detect RAM

Version 2.6.4, March 6, 2025
----------------------------

- Lower case hostname with RPI-compatibility

Version 2.6.3, February 26, 2025
----------------------------

- pin setuptools-scm version

Version 2.6.2, December 16, 2024
----------------------------

- remove typo

Version 2.6.1, December 3, 2024
----------------------------

- issue #8 - if config-param is not set, enterpret as auto-update

Version 2.6.0, November 29, 2024
----------------------------

- Remove mounted values as source for admin site URL
- remove '.git' suffix if it exists
- issue #4 - control installation/update of os2borgerpc-client location and version through config
- remove default fallback, as it is tied to a specific supplier
- Use external sources to set admin site URL
- Issue #1: automatisk versionering af klient via git tags
- Fix linting

Version 2.5.0, April 9, 2024
----------------------------

- Update NEWS.rst and version
- Add support for sms login via phone numbers with unlimited access (no quarantine)
- Add support for arbitrary login integrations
- Make the login integrations unreachable from unregistered devices
- Prevent PC info configurations from becoming too long, report last update time in human readable format
- Make client report kernel version and last update time each check-in
- 59316/hide password params
- Linting
- Add the newly required .readthedocs.yaml so docs can build again
- Retain tabs in log output
- Update NEWS.rst and version
- Client: Gather info on PC manufacturer, CPUs and RAM

Version 2.4.0, November 28, 2023
----------------------------

- Update NEWS.rst and version
- rename variable in sms_login to reflect changes in its use
- Add support for sms and booking login

Version 2.3.1, November 9, 2023
----------------------------

- Update NEWS.rst and version
- FIX: Restore setting PATH for the jobmanager cron job

Version 2.3.0-rc, September 26, 2023
----------------------------

- Update NEWS.rst and version in setup.py
- Prevent simultaneous cicero login
- Rewrite client randomize_jobmanager to also randomize on seconds
- Detect IP addresses at each check in and send them to the admin site
- Collect PC Model upon registration and send it to the adminsite
- Apply 1 suggestion(s) to 1 file(s)
- README consistency
- Makes sense, tak :)
- Reverting some changes made to OS2borgerPCAdmin constructor
- Gateway-funktionality removed.

Version 2.2.1, May 23, 2023
----------------------------

- Update NEWS.rst and version in setup.py
- Update justfile
- Update justfile
- Update translations
- Translate client

Version 2.2.0, March 9, 2023
----------------------------

- If any of the jobmanager imports fail, reinstall the client
- Update NEWS.rst and version in setup.py
- added install-tox to justfile
- Always import update_client_test
- fixup! Slow down update frequency, add code to install from testpypi instead, detach update process from jobmanager further
- Black flake8 happiness
- Slow down update frequency, add code to install from testpypi instead, detach update process from jobmanager further
- Justfile: Delete build dir, so old versions aren't potentially used for building wheel

Version 2.1.1-rc1, February 23, 2023
----------------------------

- No user-facing changes recorded in commits.

Version 2.1.1, February 23, 2023
----------------------------

- Update version and NEWS.rst
- Update justfile
- Black received new rules - rerun newest version of black
- Convert Makefile to justfile
- Push config keys: Fail on zero arguments, print help dialog with info on usage
- Minor changes to client documentation
- [#45458] Cleanup distributions in client
- Make client recognize Ubuntu 22.04

Version 2.1.0-rc1, September 15, 2022
----------------------------

- No user-facing changes recorded in commits.

Version 2.1.0, September 16, 2022
----------------------------

- Print exception if failing to check in with the adminsite
- Minor update to Makefile
- Release 2.1.0
- Update tests, so 0 is now returned by the mocked report_job_results
- Don't mark jobs sent if report_job_results failed
- Try-except around send_status_info so security scripts are still run when offline
- Run pending jobs before sending in status info from previous jobs
- Handle latin1 in job logs, use chardet for detecting encoding
- Turn README back into RST because it's used in setup.py and it expects it in that format
- Update version and NEWS.rst, and a comment in setup.py
- Update README so the table works, change to .md, remove badges from README
- Specifically exclude control chars except newlines instead of a broader approach
- Make black happier
- Sanitize log_output from scripts before sending them over XMLRPC to the adminsite
- First attempt, with commented out try-catch alternative

Version 2.0.1-rc2, August 22, 2022
----------------------------

- Turn README back into RST because it's used in setup.py and it expects it in that format

Version 2.0.1-rc1, August 20, 2022
----------------------------

- Update version and NEWS.rst, and a comment in setup.py
- Update README so the table works, change to .md, remove badges from README
- Specifically exclude control chars except newlines instead of a broader approach
- Make black happier
- Sanitize log_output from scripts before sending them over XMLRPC to the adminsite
- First attempt, with commented out try-catch alternative

Version 2.0.1, August 22, 2022
----------------------------

- Update version and NEWS.rst, and a comment in setup.py
- Update README so the table works, change to .md, remove badges from README
- Specifically exclude control chars except newlines instead of a broader approach
- Make black happier
- Sanitize log_output from scripts before sending them over XMLRPC to the adminsite
- First attempt, with commented out try-catch alternative

Version 2.0.0-rc2, July 12, 2022
----------------------------

- add comparison to newer version with semver

Version 2.0.0-rc1, July 12, 2022
----------------------------

- No user-facing changes recorded in commits.

Version 2.0.0, July 12, 2022
----------------------------

- add comparison to newer version with semver
- Release 2.0.0
- add updater
- refactor update stuff into separate module
- add print and traceback to update_client
- get instead of post for pypi check, print out versions on update check
- initial naive un-tested implementation to be talked about
- consolidate calls to send_config_keys
- update tests
- > comparison for last_check
- use second resolution and not minute for last_check comparison
- linting
- rework test for new scenario
- Update os2borgerpc/client/security/security.py
- Update os2borgerpc/client/security/security.py
- Update security.py
- Update os2borgerpc/client/security/security.py
- fix tests
- hidden passwords from outputlog and removed parameters.json when job is finished
- Document client files/programs
- only do file conversion if value is not empty string
- return None on empty lastcheck file, add tests
- refactor csv_writer.write_data
- refactor log_read variable names and add timestamp to log_content
- fixed tests
- Rewrite csv_writer and log_read
- refactor out in test_security, add test for check_security_events in succession
- Jobmanager: Don't include security events from the same minute as lastcheck (as it may repeat the same event)
- Apply 1 suggestion(s) to 1 file(s)
- remove some unneeded stuff
- make linter happy
- update tests
- Fix some bugs in changes
- add docstrings
- add ignore D105,D106 for pydocstyle
- only use client dir for pydocstyle
- linting
- add pydocstyle
- more refactoring
- Attempt at separating jobmanager and the security system
- major rewrite of security scripts portion of jobmanager
- Improve Makefile
- Add test to Makefile with description, update .gitignore for tox output files
- Update setup.py to include distro
- linting
- add more tests
- correct boolean comparisons
- test send_security_events
- make linter happy
- test collect_security_events
- remove unused variables
- add run_pending_jobs test
- add more tests
- use variable for time in tests
- use correct cov
- add coverage
- add tests
- Allow casing in computer names but still not hostnames
- Makefile: Add release to test.pypi via twine
- Silence! randomize jobmanager
- Add Makefile to build the project for easier installation for testing or release
- Consistent indentation, use less echo's
- Set /etc/hosts correctly
- make black happy
- linting
- Apply 1 suggestion(s) to 1 file(s)
- Work in progress - needs testing
- Update date to reflect reality.
- remove verbose traceback from read_property_from_file, remove (old) IOError in favor of OSError
- Update version in setup.py, please!
- Bump version, release notes.
- Update date to reflect reality.
- remove verbose traceback from read_property_from_file, remove (old) IOError in favor of OSError
- Update version in setup.py, please!
- Bump version, release notes.
- Apply 1 suggestion(s) to 1 file(s)
- add feedback from carsten
- make linter happy
- Flake8ify.
- initial commit
- Include randomize script in distribution.
- Shellcheck fix.
- [#47105] Randomize checkin times

Version 1.3.0-rc1, December 3, 2021
----------------------------

- Bump version, release notes.
- Apply 1 suggestion(s) to 1 file(s)
- add feedback from carsten
- make linter happy
- Flake8ify.
- initial commit
- Include randomize script in distribution.
- Shellcheck fix.
- [#47105] Randomize checkin times

Version 1.3.0, February 14, 2022
----------------------------

- Update date to reflect reality.
- remove verbose traceback from read_property_from_file, remove (old) IOError in favor of OSError
- Update version in setup.py, please!
- Bump version, release notes.
- Apply 1 suggestion(s) to 1 file(s)
- add feedback from carsten
- make linter happy
- Flake8ify.
- initial commit
- Include randomize script in distribution.
- Shellcheck fix.
- [#47105] Randomize checkin times

Version 1.2.0-rc1, November 24, 2021
----------------------------

- No user-facing changes recorded in commits.

Version 1.2.0, November 24, 2021
----------------------------

- Update version, release notes.
- Removed function after comment from review.
- Removed default parameter
- Remove package stuff from client.
- Rename Site ID to Site UID as that's it's name on the adminsite
- Shellcheck now passes.
- Flake8 fixes.
- Blackify python files.
- [#47115] Make pipeline pass
- Shellcheck and flake8 CI
- [#46089] Renamed function cicero_login to citizen_login
- [#46089] Added new RPC endpoint to client
- Update VERSION
- Remove superfluous line
- Ensure valid hostname incl. user friendly message
- Add reference to technical documentation on Read the Docs to README
- add missing import, print traceback

Version 1.1.3, May 7, 2021
----------------------------

- Update setup.py to new name for NEWS.rst.
- Update NEWS, version.
- fix underline header
- initial commit
- Fix with comment from review.
- Use lsb_release module to get Ubuntu version.
- Convert string to int before proceeding.

Version 1.1.2, January 29, 2021
----------------------------

- Version & release notes for version 1.1.2.
- [#41141] Number attachments so they can't overwrite one another
- [#41141] Do a slightly better job of picking out attachment basenames

Version 1.1.1, January 29, 2021
----------------------------

- Update version number and release notes.
- [#41070] Delete old security scripts in a safer way
- [#41070] Use print() rather than write() to append to the security log

Version 1.1.0, January 13, 2021
----------------------------

- Update version info, release notes.
- Updated with comments from review.
- Handle timeout correctly with config value.
- Allow configuration of job timeout.
- flake-8 compliance and a couple of merge errors fixed.
- Set package version dynamically using metadata.

Version 1.0.1, January 5, 2021
----------------------------

- Initial commit of OS2borgerPC client in its own repo.

