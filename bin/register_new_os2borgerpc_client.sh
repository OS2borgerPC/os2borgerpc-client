#!/usr/bin/env bash

SHARED_CONFIG="/tmp/os2borgerpc.conf"

# Current directory
DIR=$(dirname "${BASH_SOURCE[0]}")

while true; do
    fatal() {
        echo "Critical error. Halting registration:" "$@"
        while true; do
            echo "[R]estart or [C]ancel registration?"
            stty -echo
            read -rn 1 VALUE
            stty echo
            case "$VALUE" in
                r|R)
                    rm -f "$SHARED_CONFIG"
                    return 0 ;;
                c|C)
                    return 1 ;;
            esac
        done
    }

    # Get hold of config parameters, connect to admin system.

    if [ "$(id -u)" != "0" ]
    then
        fatal "This program must be run as root" && continue || exit 1
    fi

    echo ""

    # The following config parameters are needed to finalize the
    # installation:
    # - hostname
    #   Prompt user for new host name
    echo "Please enter a new name for this computer." \
         "The name must have a length of 1-63 characters," \
         "and valid characters are a-z, A-Z, 0-9 and hyphen (-):"
    # https://www.man7.org/linux/man-pages/man7/hostname.7.html
    read -r NEW_COMPUTER_NAME
    while [[ ! "$NEW_COMPUTER_NAME" =~ ^[0-9a-zA-Z][0-9a-zA-Z-]{1,63}$ ]]; do
        echo "Invalid computer name. Try again:"
        read -r NEW_COMPUTER_NAME
    done

    # Idea: Allow uppercase in the computername due to popular demand,
    # but lowercase it so it's a valid hostname which is case insensitive
    NEW_HOSTNAME=$(echo "$NEW_COMPUTER_NAME" | tr '[:upper:]' '[:lower:]')

    echo "$NEW_HOSTNAME" > /etc/hostname
    set_os2borgerpc_config hostname "$NEW_HOSTNAME"
    hostname "$NEW_HOSTNAME"
    sed --in-place /127.0.1.1/d /etc/hosts
    sed --in-place "2i 127.0.1.1	$NEW_HOSTNAME" /etc/hosts

    echo ""

    # - site

    echo "Enter your site UID:"
    read -r SITE
    if [[ -n "$SITE" ]]
    then
        set_os2borgerpc_config site "$SITE"
    else
        fatal "The computer cannot be registered without a site" && continue || exit 1
    fi


    # - distribution
    # Attempt to detect OS version, otherwise prompt user for it

    unset DISTRO
    if [[ -r /etc/os-release ]]; then
        # shellcheck source=/dev/null
        . /etc/os-release
        DISTRO="$ID""$VERSION_ID"
    else
        echo "We cannot detect the installed operating system." \
             "Please enter an ID for the PC distribution:"
        read -r DISTRO
    fi

    set_os2borgerpc_config distribution "$DISTRO"


    # - mac
    #   Get the mac-address
    set_os2borgerpc_config mac "$(ip addr | grep link/ether | awk 'FNR==1{print $2}')"

    echo ""


    # - admin_url
    unset ADMIN_URL
    if [[ -z "$ADMIN_URL" ]]
    then
        ADMIN_URL="https://os2borgerpc-admin.magenta.dk"
        echo "Press <ENTER> to register with the following admin portal: $ADMIN_URL."
        echo "Alternatively, type in your URL to another instance of the admin portal here:"
        read -r NEW_ADMIN_URL
        if [[ -n "$NEW_ADMIN_URL" ]]
        then
            ADMIN_URL="$NEW_ADMIN_URL"
        fi
    fi
    set_os2borgerpc_config admin_url "$ADMIN_URL"

    # - set additional config values
    PC_MODEL=$(dmidecode --type system | grep Product | cut --delimiter : --fields 2)
    [ -z "$PC_MODEL" ] && PC_MODEL="Identification failed"
    set_os2borgerpc_config pc_model "$PC_MODEL"

    PC_MANUFACTURER=$(dmidecode --type system | grep Manufacturer | cut --delimiter : --fields 2)
    [ -z "$PC_MANUFACTURER" ] && PC_MANUFACTURER="Identification failed"
    set_os2borgerpc_config pc_manufacturer "$PC_MANUFACTURER"

    # xargs is there to remove the leading space
    CPUS_BASE_INFO="$(dmidecode -t processor | grep Version | cut --delimiter ':' --fields 2 | xargs)"
    CPU_CORES="$(grep ^"core id" /proc/cpuinfo | sort -u | wc -l)"
    CPUS="$CPUS_BASE_INFO - $CPU_CORES physical cores"
    [ -z "$CPUS" ] && CPUS="Identification failed"
    set_os2borgerpc_config pc_cpus "$CPUS"

    RAM="$(LANG=c lsmem | grep "Total online" | cut --delimiter ':' --fields 2 | xargs)"
    [ -z "$RAM" ] && RAM="Identification failed"
    set_os2borgerpc_config pc_ram "$RAM"

    # OK, we got the config.
    # Do the deed.
    if ! os2borgerpc_register_in_admin "$NEW_COMPUTER_NAME"; then
        fatal "Registration failed" && continue || exit 1
    fi

    # Now setup cron job
    if [[ -f $(command -v jobmanager) ]]
    then
        # Randomize cron job to avoid everybody hitting the server the same minute
        "$DIR/randomize_jobmanager.sh" 5 > /dev/null
    fi

    break
done
