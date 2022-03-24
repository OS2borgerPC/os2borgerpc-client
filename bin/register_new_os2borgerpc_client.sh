#!/usr/bin/env bash

SHARED_CONFIG="/tmp/os2borgerpc.conf"

# Current directory
DIR=$(dirname "${BASH_SOURCE[0]}")

while true; do
    fatal() {
        echo "Kritisk fejl, stopper:" "$@"
        while true; do
            echo "[B]egynd forfra eller [S]top?"
            stty -echo
            read -rn 1 VALUE
            stty echo
            case "$VALUE" in
                b|B)
                    rm -f "$SHARED_CONFIG"
                    return 0 ;;
                s|S)
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
        fatal "Dette program skal køres som root" && continue || exit 1
    fi

    echo "Indtast gateway, tryk <ENTER> for ingen gateway eller automatisk opsætning"
    read -r GATEWAY_IP

    if [[ -z "$GATEWAY_IP" ]]
    then
        # No gateway entered by user
        GATEWAY_SITE="http://$(os2borgerpc_find_gateway 2> /dev/null)"
    else
        # User entered IP address or hostname - test if reachable by ping
        echo "Checker forbindelsen til gateway ..."
        if ! ping -c 1 "$GATEWAY_IP" > /dev/null 2>&1
        then
            fatal "Ugyldig gateway-adresse ($GATEWAY_IP)" && continue || exit 1
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
    # The following config parameters are needed to finalize the
    # installation:
    # - hostname
    #   Prompt user for new host name
    echo "Indtast venligst et nyt navn for denne computer:" \
         "Navnet skal have en længde ml. 1-63 tegn," \
         "og gyldige tegn er a-z, A-Z, 0-9 og bindestreg (-)."
    # https://www.man7.org/linux/man-pages/man7/hostname.7.html
    read -r NEW_COMPUTER_NAME
    while [[ ! "$NEW_COMPUTER_NAME" =~ ^[0-9a-zA-Z][0-9a-zA-Z-]{1,63}$ ]]; do
        echo "Ugyldigt computernavn.  Prøv igen."
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


    # - site
    #   TODO: Get site from gateway, if none present prompt user
    unset SITE
    if [[ -n "$HAS_GATEWAY" ]]
    then
        SITE="$(get_os2borgerpc_config site "$SHARED_CONFIG")"
    fi

    if [[ -z "$SITE" ]]
    then
        echo "Indtast UID for det site, computeren skal tilmeldes:"
        read -r SITE
    fi

    if [[ -n "$SITE" ]]
    then
        set_os2borgerpc_config site "$SITE"
    else
        fatal "Computeren kan ikke registreres uden site" && continue || exit 1
    fi


    # - distribution
    # Detect OS version and prompt user for verification

    unset DISTRO
    if [[ -r /etc/os-release ]]; then
        # shellcheck source=/dev/null
    	  . /etc/os-release
        if [[ "$ID" = ubuntu ]]; then
            if [[ "$VERSION_ID" = "14.04" ]]; then
                DISTRO="BIBOS14.04"
            elif [[ "$VERSION_ID" = "12.04" ]]; then
                DISTRO="BIBOS12.04"
            elif [[ "$VERSION_ID" = "16.04" ]]; then
                DISTRO="BIBOS16.04"
            elif [[ "$VERSION_ID" = "20.04" ]]; then
                DISTRO="os2borgerpc20.04"
            else
                echo "Ubuntu versionen er ikke understøttet af OS2borgerPC systemet. Du kan alligevel godt forsøge at tilmelde PC'en til admin systemet." \
                     "Indtast ID for PC'ens distribution:"
                read -r DISTRO
            fi
        else
            echo "Dette er ikke en Ubuntu maskine. OS2borgerPC systemet understøtter kun Ubuntu. Du kan alligevel godt forsøge at tilmelde PC'en til admin systemet." \
                 "Indtast ID for PC'ens distribution:"
            read -r DISTRO
        fi
    else
        echo "Vi kan ikke se hvilket operativ system der er installeret." \
             "Indtast venligst ID for PC'ens distribution:"
        read -r DISTRO
    fi

    if [[ -z "$DISTRO" ]]
    then
        echo "Indtast ID for PC'ens distribution"
        read -r DISTRO
    fi

    echo "Distributions ID: $DISTRO"

    set_os2borgerpc_config distribution "$DISTRO"


    # - mac
    #   Get the mac-address
    set_os2borgerpc_config mac "$(ip addr | grep link/ether | awk 'FNR==1{print $2}')"


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
        echo "Indtast admin-url hvis det ikke er $ADMIN_URL"
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
        fatal "Tilmelding mislykkedes" && continue || exit 1
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
