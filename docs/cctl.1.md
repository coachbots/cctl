% CCTL(1) cctl 0.3.1
% Marko Vejnovic <contact@markovejnovic.com>, Lin Liu
% Feb 2022

# NAME
cctl - coachswarm control

# SYNOPSIS
**cctl** [--help]

**cctl** {on,off,blink} [*--help*] IDs...

**cctl** {start,pause} [*--help*]

**cctl** {upload} [*--help*,*--operating-system*] PATH

**cctl** {manage}

# DESCRIPTION
**cctl** is a small utility for controlling the coachswarm. Running **cctl**
without any subcommand outputs the installed version and usage.

**cctl** supports the subcommands *on*, *off*, *blink*, *start*, *pause*,
*upload* and *manage*.

## ID-argument syntax

Any command which supports ID-based bot specification supports multiple IDs, as
well as ranges. These subcommands are *on*, *off* and *blink*. To exemplify,
you can run

**cctl** on 2 8 10-14

which will sequentially boot bots 2, 8, 10, 11, 13 and 14.

ID-argument syntax also supports the *all* keyword which will act on all
available bots:

**cctl** on *all*

boots all robots.

## cctl-on, cctl-off

**cctl {on,off}** are subcommands that turn a Coachbot on or off. They support
ID-argument syntax.

## cctl-blink

**cctl blink** is a command which turns on the LED on the specified robots.
This is done asynchronously for multiple robots so that they effectively blink
at the same time.

## cctl-start, cctl-pause

**cctl {start,pause}** control *user* code execution. Running **cctl start**
causes the user code to start on *all* booted robots. Similarly, **cctl pause**
pauses user code on all booted robots.

## cctl-upload

**cctl upload** uploads new *user* code to *all* booted robots. Note that this
command requires a positional argument specifying which file is to be treated
as user code. This file, contrary to previous iterations of the management
software, does not need to be named *usr_code.py*. A valid call to **cctl
upload** is therefore

**cctl upload my_file.py**

Moreover, this subcommand also supports the [*-o*,*--operating-system*] flag
which reuploads the operating system of all running Coachbots. The operating
system is copied from SERVER_DIR/temp/.

## cctl-manage

**cctl manage** starts the FTP server required for operating and opens the
management interface.

# CONFIGURATION

**cctl** has been designed to be highly configurable. By default, **cctl**
reads configuration values from *~/.config/coachswarm/cctl.conf* if those are
available. If not, then this script reads from */etc/coachswarm/cctl.conf*.
Finally, if neither of these are available, then sane defaults will be created
in *~/.config/coachswarm/cctl.conf*.

## cctl.conf

The **cctl.conf** follows standard *conf* file conventions and has two sections
-- **server** and **coachswarm**.

### server

The server section contains two keys:

* *interface* - The interface to be used when communicating with **coach-os**.
    This should be the interface that is connected to the same network as the
    Coachbots.
* *path* - The **full qualified path** to the legacy server directory.

### coachswarm

The coachswarm section contains configurations that are pushed to the
coachbots. There is only one key:

* *conf_path* - The **full qualified path** to the *coachswarm.conf* file.

In either case, if **cctl.conf** is ever misconfigured, deleting
*~/.config/coachswarm* and */etc/coachswarm* should give you sane defaults to
use.

# EXIT VALUES

**0**
: Successful operation.

**101**
: Configuration Error. Ensure the configuration file is properly formatted.

**102**
: Error finding the server directory. Ensure the server directory is correctly
specified in *cctl.conf*.
