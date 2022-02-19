# -*- coding: utf-8 -*-

"""This test suite runs the tests related to camera setup."""

from subprocess import PIPE, Popen
import unittest
import os
import sys

sys.path.insert(0, os.path.abspath('./src'))

from cctl.api import camera_ctl as cc


class TestCameraSetup(unittest.TestCase):
    """Tests functions pertaining to setting up the camera and the video stream
    successfully."""
    def tearDown(self) -> None:
        super().tearDown()
        cc.tear_down_processed_stream()

    def test_possible_to_get_camera_device(self):
        """Tests whether it is possible to successfully find the raw camera
        stream."""
        self.assertIsNotNone(cc.get_raw_camera_stream_device())

    def test_make_processed_stream(self):
        """Tests whether it is possible to make a processed stream regardless
        of it exists or not."""
        self.assertIsNone(cc.get_processed_camera_stream_device())
        cc.make_processed_stream()
        self.assertIsNotNone(cc.get_processed_camera_stream_device())

    def test_make_processed_stream_fails(self):
        """Tests whether make_processed_stream fails if the module is already
        loaded in the kernel."""
        if cc.get_processed_camera_stream_device() is None:
            cc.make_processed_stream()

        with self.assertRaises(cc.CameraError):
            cc.make_processed_stream()

    def test_start_processing_stream(self):
        """Tests whether the stream is successfully started."""
        if cc.get_processed_camera_stream_device() is None:
            cc.make_processed_stream()

        out_stream, _ = cc.start_processing_stream()
        with Popen(['fuser', out_stream], stdout=PIPE) as fuser_call:
            self.assertIsNotNone(fuser_call.stdout)
            assert fuser_call.stdout is not None
            fuser_out = fuser_call.stdout.read().strip()
            self.assertIsNotNone(fuser_out)
