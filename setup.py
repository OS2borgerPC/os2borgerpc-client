from setuptools import setup

with open("README.rst", "r") as fh:
    long_description = fh.read()

setup(
    # Keep this name in sync with the one in os2borgerpc_client/jobmanager.py
    name="os2borgerpc_client",
    version="2.4.1",
    description="Client for the OS2borgerPC system",
    long_description=long_description,
    url="https://github.com/OS2borgerPC/",
    author="Magenta ApS",
    author_email="info@magenta-aps.dk",
    license="GPLv3",
    packages=["os2borgerpc.client", "os2borgerpc.client.security"],
    install_requires=["PyYAML", "distro", "requests", "semver", "chardet"],
    scripts=[
        "bin/get_os2borgerpc_config",
        "bin/set_os2borgerpc_config",
        "bin/os2borgerpc_register_in_admin",
        "bin/os2borgerpc_push_config_keys",
        "bin/jobmanager",
        "bin/register_new_os2borgerpc_client.sh",
        "bin/admin_connect.sh",
        "bin/randomize_jobmanager.sh",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
    ],
    zip_safe=False,
    python_requires=">=3.6",
)
