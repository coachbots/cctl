#!/usr/bin/env bash

INDEV=/dev/video-cctl-overhead-raw
OUTDEV=/dev/video72
K1=$(grep -oP '^lens_k1=\K.*$' /etc/coachswarm/cctld.conf)
K2=$(grep -oP '^lens_k2=\K.*$' /etc/coachswarm/cctld.conf)
CX=$(grep -oP '^lens_cx=\K.*$' /etc/coachswarm/cctld.conf)
CY=$(grep -oP '^lens_cy=\K.*$' /etc/coachswarm/cctld.conf)

ffmpeg -hwaccel vdpau -re \
    -i $INDEV \
    -map 0:v -vf \
    lenscorrection=k1=$K1:k2=$K2:cx=$CX:cy=$CY,format=yuv420p \
    -f v4l2 $OUTDEV
