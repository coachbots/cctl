PYTHON=python3

.PHONY: build manpage docs install uninstall install-docs uninstall-docs \
	test-feature test-unit test

build:
	$(PYTHON) -m build

manpage:
	mkdir -p build
	pandoc docs/cctl.1.md -s -t man -o build/cctl.1
	gzip -f build/cctl.1
	mkdir -p dist/
	mv build/cctl.1.gz dist/cctl.1.gz
	rm -r build

docs: manpage
	cd docs && $(MAKE) html

install:
	$(PYTHON) -m pip install dist/cctl-*.whl --force-reinstall

uninstall:
	$(PYTHON) -m pip uninstall cctl

# The uninstall-docs call here is made to ensure that the old doctree gets
# cleaned up.
install-docs: uninstall-docs
	install -Dm644 dist/cctl.1.gz /usr/local/man/man1/cctl.1.gz
	install -Dm644 cctl-completion.bash /etc/bash_completion.d/cctl.bash
	cd docs/build/html && find . -type f -exec install -Dm644 \
		"{}" "/usr/share/doc/cctl/{}" \;

uninstall-docs:
	rm -f /usr/local/man/man1/cctl.1.gz
	rm -f /etc/bash_completion.d/cctl.bash
	rm -rf /usr/share/doc/cctl

test-feature:
	$(PYTHON) -m unittest discover tests/feature

test-unit:
	$(PYTHON) -m unittest discover tests/unit

test: test-feature test-unit
