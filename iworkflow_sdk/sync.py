import requests
import time
import logging

from . exceptions import BigipSyncException
from . import LOGGER_NAME

BIGIP_SAVE_ENDPOINT = "/mgmt/tm/sys/config"
BIGIP_SYNC_ENDPOINT = "/mgmt/tm/cm/config-sync"
BIGIP_DEVICE_ENDPOINT = "/mgmt/tm/cm/device"
BIGIP_STATUS_ENDPOINT = "/mgmt/tm/cm/sync-status"

BIGIP_FAILOVER_STATE = "failoverState"
BIGIP_STANDBY_STATE = "standby"
BIGIP_MGMT_IP = "managementIp"
BIGIP_ACTIVE_STATE = "active"
BIGIP_SELF_DEVICE = "selfDevice"
BIGIP_ITEMS = "items"
BIGIP_CMD = "command"
BIGIP_CMD_SAVE = "save"
BIGIP_CMD_RUN = "run"
BIGIP_CMD_UTIL_ARGS = "utilCmdArgs"
BIGIP_SYNC_TO_GROUP = "to-group {0}"
BIGIP_ENTRIES = "entries"
BIGIP_NESTED_STATS = "nestedStats"
BIGIP_STATUS = "status"
BIGIP_SUMMARY = "summary"
BIGIP_DESCRIPTION = "description"
BIGIP_IN_SYNC = "In Sync"

log = logging.getLogger(LOGGER_NAME)


def do_sync(ip, sync_group, user, password, retry_timer):
    HttpSession.setup_session(user, password)

    active_ip = _get_device(ip)

    _request_save(active_ip)
    _request_sync(active_ip, sync_group)

    _await_status(active_ip, retry_timer)


def _get_device(ip):
    resp = _do_get(ip, BIGIP_DEVICE_ENDPOINT)

    return _determine_active_device(ip, resp)


def _determine_active_device(current_ip, resp_devices):
    try:
        if _get_self_device(resp_devices)\
                .get(BIGIP_FAILOVER_STATE) == \
                BIGIP_STANDBY_STATE:
            log.warn("Device is standby unit")
            return next(
                dev.get(BIGIP_MGMT_IP)
                for dev in resp_devices.get(BIGIP_ITEMS)
                if dev.get(BIGIP_FAILOVER_STATE) ==
                BIGIP_ACTIVE_STATE
                )
        else:
            return current_ip
    except Exception:
        raise BigipSyncException("Cannot find an active device")


def _get_self_device(devices):
    self_device_idx = 0

    while True:
        try:
            if devices \
                .get(BIGIP_ITEMS) \
                .get(self_device_idx) \
                .get(BIGIP_SELF_DEVICE) \
                    == "true":
                return devices.get(BIGIP_ITEMS).get(self_device_idx)
            else:
                self_device_idx = + 1
        except Exception:
            raise BigipSyncException("Cannot find an active device")


def _request_save(ip):
    payload = dict()
    payload[BIGIP_CMD] = BIGIP_CMD_SAVE

    _do_post(ip, BIGIP_SAVE_ENDPOINT, payload)


def _request_sync(ip, sync_group):
    payload = dict()
    payload[BIGIP_CMD] = BIGIP_CMD_RUN
    payload[BIGIP_CMD_UTIL_ARGS] = \
        BIGIP_SYNC_TO_GROUP.format(sync_group)

    _do_post(ip, BIGIP_SAVE_ENDPOINT, payload)


def _do_post(ip, endpoint, payload):
    resp = HttpSession.session.post(
        "https://{0}{1}".format(ip, endpoint),
        json=payload
    )

    if resp.status_code != requests.codes.OK:
        raise BigipSyncException("Received unsupported status code={}".format(
            resp.status_code
        ))

    return resp


def _do_get(ip, endpoint):
    resp = HttpSession.session.get("https://{0}{1}".format(ip, endpoint))

    if resp.status_code != requests.codes.OK:
        raise BigipSyncException("")

    return resp


def _await_status(ip, retry_timer):
    while True:
        status_json = _do_get(ip, BIGIP_STATUS_ENDPOINT).json()
        entries = status_json \
            .get(BIGIP_ENTRIES) \
            .get(
                ('https://{0}{1}/0'.format("localhost",
                                           BIGIP_STATUS_ENDPOINT))) \
            .get(BIGIP_NESTED_STATS) \
            .get(BIGIP_ENTRIES)

        status = entries.get(BIGIP_STATUS) \
            .get(BIGIP_DESCRIPTION)
        summary = entries.get(BIGIP_SUMMARY) \
            .get(BIGIP_DESCRIPTION)
        log.info("Status: {0}: {1}".format(status, summary))
        if status == BIGIP_IN_SYNC:
            break
        else:
            log.info("Retry in {0}s".format(retry_timer))
            time.sleep(retry_timer)


class HttpSession:
    session = None

    @classmethod
    def setup_session(cls, user, password):
        cls.session = requests.session()
        cls.session.auth = (user, password)
        cls.session.verify = False
        cls.session.headers.update({'Content-Type': 'application/json'})
