"""Module for the admin client."""

import xmlrpc.client


def get_default_admin(verbose=False):
    """Return the default OS2borgerPCAdmin object."""
    from os2borgerpc.client.config import OS2borgerPCConfig

    conf_data = OS2borgerPCConfig().get_data()
    admin_url = conf_data.get("admin_url", "https://os2borgerpc.magenta-aps.dk")
    xml_rpc_url = conf_data.get("xml_rpc_url", "/admin-xml/")
    return OS2borgerPCAdmin("".join([admin_url, xml_rpc_url]), verbose=verbose)


class OS2borgerPCAdmin(object):
    """XML-RPC client class for communicating with admin system."""

    def __init__(self, url, verbose=False):
        """According to D107 docstrings are required."""
        rpc_args = {"verbose": verbose, "allow_none": True}
        self._rpc_srv = xmlrpc.client.ServerProxy(url, **rpc_args)

    def register_new_computer(self, mac, name, distribution, site, configuration):
        """register_new_computer from the admin site rpc module."""
        return self._rpc_srv.register_new_computer(
            mac, name, distribution, site, configuration
        )

    def send_status_info(self, pc_uid, package_data, job_data, update_required=None):
        """send_status_info from the admin site rpc module."""
        return self._rpc_srv.send_status_info(
            pc_uid, package_data, job_data, update_required
        )

    def get_instructions(self, pc_uid):
        """get_instructions from the admin site rpc module."""
        return self._rpc_srv.get_instructions(pc_uid)

    def push_config_keys(self, pc_uid, config_dict):
        """push_config_keys from the admin site rpc module."""
        return self._rpc_srv.push_config_keys(pc_uid, config_dict)

    def push_security_events(self, pc_uid, csv_data):
        """push_security_events from the admin site rpc module."""
        return self._rpc_srv.push_security_events(pc_uid, csv_data)

    def citizen_login(self, username, password, site, prevent_dual_login=False):
        """citizen_login from the admin site rpc module."""
        return self._rpc_srv.citizen_login(username, password, site, prevent_dual_login)

    def citizen_logout(self, citizen_hash):
        """citizen_logout from the admin site rpc module."""
        return self._rpc_srv.citizen_logout(citizen_hash)

    def sms_login(self, phone_number, message, site, require_booking, pc_name):
        """sms_login from the admin site rpc module."""
        return self._rpc_srv.sms_login(
            phone_number, message, site, require_booking, pc_name
        )

    def sms_login_finalize(self, phone_number, site, require_booking, save_log):
        """sms_login_finalize from the admin site rpc module."""
        return self._rpc_srv.sms_login_finalize(
            phone_number, site, require_booking, save_log
        )

    def sms_logout(self, citizen_hash, log_id):
        """sms_logout from the admin site rpc module."""
        return self._rpc_srv.sms_logout(citizen_hash, log_id)
