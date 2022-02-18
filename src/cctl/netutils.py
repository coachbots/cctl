# -*- coding: utf-8 -*-

"""Exposes network utilities."""

from contextlib import contextmanager
import logging
import socket
import struct
import asyncio
import fcntl
import platform
import subprocess
from typing import Union
import paramiko
from paramiko.client import SSHClient
from paramiko import WarningPolicy

from cctl.api import configuration
from cctl.res import RES_STR

SIOCGIFADDR = 0x8915  # See man netdevice 7
SIOCGIFBRDADDR = 0x8919  # See man netdevice 7


async def async_ping(hostname: str, count: int = 1,
                     max_timeout: float = 1) -> int:
    """Asynchronously pings a hostname.

    Parameters:
        hostname (str): The target to ping
        count (int): The number of times to ping it.
        max_timeout (float): The maximum number of seconds before ping gives
            up.

    Returns:
        int: The ping status code.
    """
    return await (await asyncio.create_subprocess_exec(
        'ping',
        '-n' if platform.system().lower() == 'windows' else '-c',
        str(count),
        '-w', str(max_timeout),
        hostname,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )).wait()


def ping(hostname: str, count: int = 1) -> int:
    """Pings a hostname.

    Parameters:
        hostname (str): The target to ping
        count (int): The number of times to ping it.

    Returns:
        int: The ping status code.
    """

    return asyncio.get_event_loop().run_until_complete(
        async_ping(hostname, count))


async def async_host_is_reachable(hostname: str,
                                  max_attempts: int = 1) -> bool:
    """Asynchronously checks whether a host is reachable via ping.

    Parameters:
        hostname (str): The target to ping.
        max_attempts (int): The maximum number attempts you are willing to
            ping.

    Returns:
        bool: Whether the host was reachable on any attempt.
    """
    for _ in range(max_attempts):
        if (await async_ping(hostname, 1)) == 0:
            return True
    return False


def host_is_reachable(hostname: str, max_attempts: int = 3) -> bool:
    """Checks whether a host is reachable via ping.

    Parameters:
        hostname (str): The target to ping.
        max_attempts (int): The maximum number attempts you are willing to
            ping.

    Returns:
        bool: Whether the host was reachable on any attempt.
    """
    return asyncio.get_event_loop().run_until_complete(
        async_host_is_reachable(hostname, max_attempts))


@contextmanager
def sftp_client(hostname: str, *args, **kwargs):
    """Opens up an SFTP client with sane defaults.

    These defaults are:
        * Read key from the user configuration.
    """
    key = configuration.get_path_to_ssh_key()

    client = SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(WarningPolicy())

    try:
        client.connect(hostname, key_filename=key)
    except paramiko.AuthenticationException as auth_ex:
        logging.error(RES_STR['ssh_auth_error'], key)
        raise auth_ex

    try:
        m_sftp_client = client.open_sftp(*args, **kwargs)
        try:
            yield m_sftp_client
        finally:
            sftp_client.close()
    finally:
        client.close()


def read_remote_file(hostname: str, remote_path: str,
                     mode: str = 'rb') -> bytes:
    """Reads a remote file in full.

    Parameters:
        hostname (str): The hostname of the remote.
        remote_path (str): The path to the remote file.
        mode (str): The mode to read the file in, 'rb' by default.

    Returns:
        bytes: The file contents.
    """
    with sftp_client(hostname) as client:
        with client.open(remote_path, mode) as r_file:
            return r_file.read()


def write_remote_file(hostname: str, remote_path: str,
                      data: Union[bytes, str], mode: str = 'wb') -> None:
    """Writes some data to a possibly remote file.

    Parameters:
        hostname (str): The hostname of the remote.
        remote_path (str): The path to the remote file.
        data (bytes | str): The data to write.
        mode (str): The mode to write the file in, 'wb' by default.
    """

    with sftp_client(hostname) as client:
        with client.open(remote_path, mode) as r_file:
            r_file.write(data)


def get_ip_address(ifname: str) -> str:
    """Returns the ip address of the specified interface name.

    Parameters:
        ifname (str): The target interface name.

    Returns:
        str: The IP address of that interface.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        ip_a = socket.inet_ntoa(fcntl.ioctl(
            sock.fileno(),
            SIOCGIFADDR,
            struct.pack('256s', bytes(ifname[:15], 'utf-8'))
        )[20:24])

        return ip_a


def get_broadcast_address(ifname: str) -> str:
    """Returns the broadcast address of the specified interface name.

    Note:
        On a network, the broadcast address is the address that, which sent to,
        ensures that all devices on the network receive the message sent. In
        other words, if you send to this address, the router ensures that every
        device will get the memo.

    Parameters:
        ifname (str): The target interface name.

    Returns:
        str: The broadcast IP address of that interface.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        ip_a = socket.inet_ntoa(fcntl.ioctl(
            sock.fileno(),
            SIOCGIFBRDADDR,
            struct.pack('256s', bytes(ifname[:15], 'utf-8'))
        )[20:24])

        return ip_a
