"""Module for the admin client."""

import os
import re
import secrets
import xmlrpc.client


DEFAULT_CLIENT_KEY_PATH = "/etc/os2borgerpc/client-key.key"


def get_default_admin(verbose=False):
    """Return the default OS2borgerPCAdmin object."""
    from os2borgerpc.client.config import OS2borgerPCConfig

    conf_data = OS2borgerPCConfig().get_data()
    admin_url = conf_data.get("admin_url")
    xml_rpc_url = conf_data.get("xml_rpc_url", "/admin-xml/")
    return OS2borgerPCAdmin("".join([admin_url, xml_rpc_url]), verbose=verbose)


class OS2borgerPCAdmin(object):
    """XML-RPC client class for communicating with admin system."""

    def __init__(self, url, verbose=False, client_key_path=DEFAULT_CLIENT_KEY_PATH):
        """According to D107 docstrings are required."""
        self.client_key_path = client_key_path
        self._rpc_supports_client_key = None
        self.generate_client_key_if_not_exists()
        rpc_args = {"verbose": verbose, "allow_none": True}
        self._rpc_srv = xmlrpc.client.ServerProxy(url, **rpc_args)

    def read_client_key(self):
        """Read and return the local client key."""
        with open(self.client_key_path, "r") as fh:
            return fh.read().strip()

    def generate_client_key_if_not_exists(self):
        """Create a random client key file if one does not already exist."""
        if os.path.exists(self.client_key_path):
            return

        client_key_dir = os.path.dirname(self.client_key_path)
        if client_key_dir:
            os.makedirs(client_key_dir, mode=0o700, exist_ok=True)

        random_hex = secrets.token_hex(32)
        with open(self.client_key_path, "w") as fh:
            fh.write(random_hex)
        os.chmod(self.client_key_path, 0o600)

    def _is_legacy_signature_fault(self, fault):
        """Return True when fault indicates incompatible RPC argument count."""
        text = fault.faultString.lower()
        patterns = [
            r"takes .* positional arguments? but .* were given",
            r"takes exactly .* arguments? \(.* given\)",
            r"not enough arguments",
            r"too many arguments",
        ]
        return any(re.search(pattern, text) for pattern in patterns)

    def _rpc_call(self, method_name, *args):
        """Call RPC method and append client key when supported."""
        method = getattr(self._rpc_srv, method_name)

        if self._rpc_supports_client_key is False:
            return method(*args)

        client_key = self.read_client_key()
        try:
            result = method(*args, client_key)
            self._rpc_supports_client_key = True
            return result
        except xmlrpc.client.Fault as fault:
            if self._rpc_supports_client_key is None and self._is_legacy_signature_fault(fault):
                self._rpc_supports_client_key = False
                return method(*args)
            raise

    def register_new_computer(self, mac, name, distribution, site, configuration):
        """register_new_computer from the admin site rpc module."""
        return self._rpc_call(
            "register_new_computer",
            mac, name, distribution, site, configuration
        )

    def send_status_info(self, pc_uid, package_data, job_data, update_required=None):
        """send_status_info from the admin site rpc module."""
        return self._rpc_call(
            "send_status_info",
            pc_uid, package_data, job_data, update_required
        )

    def get_instructions(self, pc_uid):
        """get_instructions from the admin site rpc module."""
        return self._rpc_call("get_instructions", pc_uid)

    def push_config_keys(self, pc_uid, config_dict):
        """push_config_keys from the admin site rpc module."""
        return self._rpc_call("push_config_keys", pc_uid, config_dict)

    def push_security_events(self, pc_uid, csv_data):
        """push_security_events from the admin site rpc module."""
        return self._rpc_call("push_security_events", pc_uid, csv_data)

    def citizen_login(self, username, password, pc_uid, prevent_dual_login=False):
        """citizen_login from the admin site rpc module."""
        return self._rpc_call(
            "citizen_login",
            username, password, pc_uid, prevent_dual_login
        )

    def citizen_logout(self, citizen_hash):
        """citizen_logout from the admin site rpc module."""
        return self._rpc_call("citizen_logout", citizen_hash)

    def general_citizen_login(self, pc_uid, integration, value_dict):
        """general_citizen_login from the admin site rpc module."""
        return self._rpc_call("general_citizen_login", pc_uid, integration, value_dict)

    def general_citizen_logout(self, citizen_hash, log_id):
        """general_citizen_logout from the admin site rpc module."""
        return self._rpc_call("general_citizen_logout", citizen_hash, log_id)

    def sms_login(
        self,
        phone_number,
        message,
        pc_uid,
        require_booking,
        pc_name,
        allow_idle_login=False,
        login_duration=None,
        quarantine_duration=None,
        unlimited_access=False,
    ):
        """sms_login from the admin site rpc module."""
        return self._rpc_call(
            "sms_login",
            phone_number,
            message,
            pc_uid,
            require_booking,
            pc_name,
            allow_idle_login,
            login_duration,
            quarantine_duration,
            unlimited_access,
        )

    def sms_login_finalize(
        self,
        phone_number,
        pc_uid,
        require_booking,
        save_log,
        allow_idle_login=False,
        login_duration=None,
        quarantine_duration=None,
    ):
        """sms_login_finalize from the admin site rpc module."""
        return self._rpc_call(
            "sms_login_finalize",
            phone_number,
            pc_uid,
            require_booking,
            save_log,
            allow_idle_login,
            login_duration,
            quarantine_duration,
        )

    def sms_logout(self, citizen_hash, log_id):
        """sms_logout from the admin site rpc module."""
        return self._rpc_call("sms_logout", citizen_hash, log_id)
