# -*- coding: utf-8 -*-

"""Exposes network utilities."""

from subprocess import call
import platform
from paramiko.client import SSHClient


def ping(hostname: str, count: int = 1) -> int:
    """Pings a hostname.

    Parameters:
        hostname (str): The target to ping
        count (int): The number of times to ping it.

    Returns:
        int: The ping status code.
    """

    return call(['ping',
                 '-n' if platform.system().lower() == 'windows' else '-c',
                 str(count),
                 hostname])


def host_is_reachable(hostname: str, max_attempts: int = 3) -> bool:
    """Checks whether a host is reachable via ping.

    Parameters:
        hostname (str): The target to ping.
        max_attempts (int): The maximum number attempts you are willing to
            ping.

    Returns:
        bool: Whether the host was reachable on any attempt.
    """
    return any(ping(hostname, 1) == 0 for _ in range(max_attempts))


def read_remote_file(hostname: str, remote_path: str) -> bytes:
    """Reads a remote file in full.

    Parameters:
        hostname (str): The hostname of the remote.
        remote_path (str): The path to the remote file.

    Returns:
        bytes: The file contents.
    """
    client = SSHClient()
    client.load_system_host_keys()
    client.connect(hostname)

    sftp_client = client.open_sftp()
    data = sftp_client.open(remote_path).read()
    sftp_client.close()
    client.close()

    return data
