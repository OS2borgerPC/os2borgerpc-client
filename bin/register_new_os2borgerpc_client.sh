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

    # Attempt to get shared config file from gateway.
    # It this fails, the user must enter the corresponding data (site and
    # admin_url) manually.
    if [ "$(id -u)" != "0" ]
    then
        fatal "This program must be run as root" && continue || exit 1
    fi

    echo "Press <ENTER> for no gateway or automatic setup. Alternatively, enter a gateway address:"
    read -r GATEWAY_IP

    if [[ -z "$GATEWAY_IP" ]]
    then
        # No gateway entered by user
        GATEWAY_SITE="http://$(os2borgerpc_find_gateway 2> /dev/null)"
    else
        # User entered IP address or hostname - test if reachable by ping
        echo "Checking connection to the gateway ..."
        if ! ping -c 1 "$GATEWAY_IP" > /dev/null 2>&1
        then
            fatal "Invalid gateway address ($GATEWAY_IP)" && continue || exit 1
        else
            echo "OK"
        fi
        # Gateway is pingable - we assume that means it's OK.
        GATEWAY_SITE="http://$GATEWAY_IP"
        set_os2borgerpc_config gateway "$GATEWAY_IP"
    fi

    curl -s "$GATEWAY_SITE/os2borgerpc.conf" -o "$SHARED_CONFIG"

    unset HAS_GATEWAY
    if [[ -f "$SHARED_CONFIG" ]]
    then
        HAS_GATEWAY=1
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
    #   TODO: Get site from gateway, if none present prompt user
    unset SITE
    if [[ -n "$HAS_GATEWAY" ]]
    then
        SITE="$(get_os2borgerpc_config site "$SHARED_CONFIG")"
    fi

    if [[ -z "$SITE" ]]
    then
        echo "Enter your site UID:"
        read -r SITE
    fi

    if [[ -n "$SITE" ]]
    then
        set_os2borgerpc_config site "$SITE"
    else
        fatal "The computer cannot be registered without a site" && continue || exit 1
    fi


    # - distribution
    # Detect OS version and prompt user for verification

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
    #   Get from gateway, otherwise prompt user.
    unset ADMIN_URL
    if [[ -n "$HAS_GATEWAY" ]]
    then
        ADMIN_URL=$(get_os2borgerpc_config admin_url "$SHARED_CONFIG")
    fi
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

    # OK, we got the config.
    # Do the deed.
    if ! os2borgerpc_register_in_admin "$NEW_COMPUTER_NAME"; then
        fatal "Registration failed" && continue || exit 1
    fi

    # Now setup cron job
    if [[ -f $(command -v jobmanager) ]]
    then
        echo 'PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin' > /etc/cron.d/os2borgerpc-jobmanager
        echo "*/5 * * * * root $(command -v jobmanager)" >> /etc/cron.d/os2borgerpc-jobmanager
    fi

    # Now randomize cron job to avoid everybody hitting the server every five minutes.
    "$DIR/randomize_jobmanager.sh" 5 > /dev/null

    break
done
