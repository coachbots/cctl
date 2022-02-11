"""This module exposes functions for controlling camera source and sink."""

import logging
import sys
import os
from os import path
from typing import Optional
from subprocess import call

from cctl.res import ERROR_CODES, RES_STR


def _get_camera_device_by_name(name: str) -> Optional[str]:
    video_descriptors = path.join('/', 'sys', 'class', 'video4linux')
    for video_dev in os.listdir(video_descriptors):
        video_name_file = path.join(video_descriptors, video_dev, 'name')
        video_name = None
        with open(video_name_file, 'r') as vfile:
            video_name = vfile.read()

        if video_name in name:
            return path.join('/', 'dev', video_dev)

    return None


def get_raw_camera_stream_device(
        target_name: str = 'Piwebcam: UVC Camera') -> Optional[str]:
    """
    Parameters:
        target_name: The name of the raw camera stream device.

    Returns:
        The path to the webcam stream device if it is available, none,
        otherwise.
    """
    return _get_camera_device_by_name(target_name)


def get_processed_camera_stream_device(
        target_name: str = "coachcam_stream_processed") -> Optional[str]:
    """
    Parameters:
        target_name: The name of the processed camera stream device.

    Returns:
        The path to the processed stream device if it is available, none,
        otherwise.
    """
    return _get_camera_device_by_name(target_name)


def make_processed_stream(
        target_name: str = "coachcam_stream_processed") -> None:
    """Attempts to make a stream using the loopback device."""
    result = call(['modprobe', 'v4l2loopback', f'card_label="{target_name}"'])

    if result != 0:
        logging.error(RES_STR['processed_stream_creating_error'])
        sys.exit(ERROR_CODES['processed_stream_creating_error'])


def start_processing_stream(k_1: float = -0.22, k_2: float = -0.022,
                            c_x: float = .52, c_y: float = 0.5) -> None:
    """
    Starts the appropriate `ffmpeg` stream that does all live-video
    corrections.

    Parameters:
        k1: The first correction parameter
        k2: The second correction parameter
        cx: The relative lens focal center on the x-axis
        cy: The relative lens focal center on the y-axis

    Note:
        This implementation merely calls `ffmpeg` as a subprocess.
    """

    in_stream = get_raw_camera_stream_device()
    out_stream = get_processed_camera_stream_device()

    assert in_stream is not None
    assert out_stream is not None

    result = call(['ffmpeg', '-re', '-i', in_stream, '-map', '0:v',
                   '-vf', f'"lenscorrection=k1={k_1}:k2={k_2}:' +
                   f'cx={c_x}:cy={c_y}",format=yuv420p',
                   '-f', 'v4l2', out_stream])

    if result != 0:
        logging.error(RES_STR['unknown_camera_error'])
        sys.exit(ERROR_CODES['unknown_camera_error'])
