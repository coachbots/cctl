#!/usr/bin/env python

"""This module exposes the configuration cctl uses."""


class Configuration:
    class CCTLD:
        @property
        def request_host(self) -> str:
            return ''

        @property
        def state_feed_host(self) -> str:
            return ''

    @property
    def cctld(self) -> 'Configuration.CCTLD':
        return Configuration.CCTLD()
