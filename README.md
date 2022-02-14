# cctl

**cctl** is a utility and package for host control of the Coachbots at
Northwestern University, CRBS.

## Installation

**cctl** does **not** ship `dpkg` packages so you need to manually build it and
install it.

### Dependencies

To get started, make sure you have

```bash
sudo apt-get install python3.6 python ffmpeg pandoc v4l2loopback-dkms
```

### Installation

After you install these, you can clone the repo and install it:

```bash
git clone git@github.com:markovejnovic/cctl.git
cd cctl
make
sudo make install

make docs
sudo make install-docs
```

This will automatically install **cctl** as well as the accompanying
documentation. Note the `install-docs` target installs auto-completion.

### Removal

To remove the software you can run:

```bash
sudo make uninstall
sudo make uninstall-docs
```

## Usage

The usage is described with the `--help` flag.

Simply run:
```bash
cctl --help
```
or
```bash
cctl {command} --help
```
for usage information.

Manpages exist and can be viewed with `man cctl`. These fully document the
operation of `cctl`.

## Documentation

The code is fully documented and can be viewed by running:

```bash
make docs
sudo make install-docs
```

Then you can open the docs with your browser in
[/usr/share/doc/cctl/index.html](file:///usr/share/doc/cctl/index.html).
