# cctl

**cctl** is a utility and package for host control of the Coachbots at
Northwestern University, CRBS.

## Installation

**cctl** does **not** ship `dpkg` packages so you need to manually build it and
install it.

### Dependencies

To get started, make sure you have

```bash
sudo apt-get install python3.8 python ffmpeg pandoc v4l2loopback-dkms
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

## Documentation.

The documentation is currently hosted on
[st.iris.markovejnovic.com/cctl-docs](https://st.iris.markovejnovic.com/cctl-docs/).

## Tests

Running tests is a mildly involved process. All tests are currently feature
tests, meaning that it is only possible to run tests in the target environment.
In other words, in order to get valid test results, you must run them
exclusively on the computer controlling the coachbots. You can then simply run:

```bash
make test
```

to run all tests.

## Documentation

The code is fully documented and can be viewed by running:

```bash
make docs
sudo make install-docs
```

Then you can open the docs with your browser in
[/usr/share/doc/cctl/index.html](file:///usr/share/doc/cctl/index.html).

Prebuilt documentation is available here:

[coach-os-docs](https://st.iris.markovejnovic.com/coach-os-docs/index.html)

[cctl-docs](https://st.iris.markovejnovic.com/cctl-docs/index.html)

[Coachbot Handbook](https://docs.google.com/document/d/1Kd5gWVj3HDt77QHQix5gH5CfSBZLwaTMpmtrRFf8U_U/edit)

