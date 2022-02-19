"""This module exposes functions for controlling camera source and sink."""

from enum import IntEnum
import logging
import sys
import os
from os import path
from typing import Optional, Tuple
from subprocess import DEVNULL, PIPE, Popen, call
from cctl.api.configuration import get_camera_device_name, \
    get_camera_lens_correction_factors, get_processed_video_device_name

from cctl.res import ERROR_CODES, RES_STR


class CameraEnum(IntEnum):
    """A small enumerator for storing supported cameras."""
    CAMERA_RAW = 0
    CAMERA_CORRECTED = 1


class CameraError(ValueError):
    """Represents a camera error that may have occurred.

    Parameters:
        identifier: A variable for holding which camera errored out. Usually,
        this could be the number at the end of /dev/videoX or an IntEnum value.
    """
    def __init__(self, identifier: int) -> None:
        super().__init__()
        self.identifier = identifier


def _get_camera_device_by_name(name: str) -> Optional[str]:
    video_descriptors = path.join('/', 'sys', 'class', 'video4linux')
    for video_dev in os.listdir(video_descriptors):
        video_name_file = path.join(video_descriptors, video_dev, 'name')
        video_name = None
        with open(video_name_file, 'r') as vfile:
            video_name = vfile.read().strip()

        if video_name.find(name) != -1:
            return path.join('/', 'dev', video_dev)

    return None


def get_raw_camera_stream_device(
        target_name: str = get_camera_device_name()) -> Optional[str]:
    """
    Parameters:
        target_name: The name of the raw camera stream device.

    Returns:
        The path to the webcam stream device if it is available, none,
        otherwise.
    """
    return _get_camera_device_by_name(target_name)


def get_processed_camera_stream_device(
        target_name: str = get_processed_video_device_name()) \
        -> Optional[str]:
    """
    Parameters:
        target_name: The name of the processed camera stream device.

    Returns:
        The path to the processed stream device if it is available, none,
        otherwise.
    """
    return _get_camera_device_by_name(target_name)


def make_processed_stream(
        target_name: str = get_processed_video_device_name()) -> None:
    """Attempts to make a stream using the loopback device."""
    modprobe_command = ['modprobe', '--first-time', 'v4l2loopback',
                        f'card_label="{target_name}"']
    with Popen(modprobe_command, stderr=PIPE) as probe_attempt:
        _, out_err = probe_attempt.communicate()
        if 'Operation not permitted' in str(out_err):
            # We don't have permissions. Let's ask the user to give us
            # permissions.
            logging.info(RES_STR['cam_modprobe_permission'],
                         ' '.join(modprobe_command))
            # -k forces sudo to ask for password.
            if call(['sudo', '-k'] + modprobe_command) == 0:
                return
        if 'Module already in kernel' in str(out_err):
            # The module is already in kernel. The user should get rid of it.
            # We can't because we might break another loopback stream.
            logging.error(RES_STR['v4l2loopback_already_loaded'])
            raise CameraError(CameraEnum.CAMERA_CORRECTED)

        if probe_attempt.returncode == 0:
            return

    logging.error(RES_STR['processed_stream_creating_error'])
    raise CameraError(CameraEnum.CAMERA_CORRECTED)


def start_processing_stream(
        k_1: float = get_camera_lens_correction_factors()[0],
        k_2: float = get_camera_lens_correction_factors()[1],
        c_x: float = get_camera_lens_correction_factors()[2],
        c_y: float = get_camera_lens_correction_factors()[3]) -> Tuple[str,
                                                                       int]:
    """
    Starts the appropriate `ffmpeg` stream that does all live-video
    corrections.

    Parameters:
        k1: The first correction parameter
        k2: The second correction parameter
        cx: The relative lens focal center on the x-axis
        cy: The relative lens focal center on the y-axis

    Returns:
        A tuple containing the full path to the video device and the PID of the
        process.

    Raises:
        ValueError if either of the streams do not have an appropriate device.

    Note:
        This implementation merely calls `ffmpeg` as a subprocess.
    """

    in_stream = get_raw_camera_stream_device()
    out_stream = get_processed_camera_stream_device()

    if in_stream is None:
        raise CameraError(CameraEnum.CAMERA_RAW.value)

    if out_stream is None:
        raise CameraError(CameraEnum.CAMERA_CORRECTED.value)

    command = ['ffmpeg', '-re', '-i', in_stream, '-map', '0:v', '-vf',
               f'lenscorrection=k1={k_1}:k2={k_2}:' +
               f'cx={c_x}:cy={c_y},format=yuv420p', '-f', 'v4l2', out_stream]

    logging.info(RES_STR['running_ffmpeg'], ' '.join(command), out_stream)
    pid = Popen(command, stdout=DEVNULL, stderr=DEVNULL).pid

    return out_stream, pid


def start_processed_preview() -> Tuple[str, int]:
    """Attempts to start the processed preview.

    Returns:
        The device path and the pid of ffplay.

    Raises:
        CameraError if this is not possible.
    """
    device = get_processed_camera_stream_device()

    if device is None:
        raise CameraError(CameraEnum.CAMERA_CORRECTED.value)

    command = ['ffplay', device]
    pid = Popen(command, stdout=DEVNULL, stderr=DEVNULL).pid

    return device, pid
