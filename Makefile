PYTHON_VER=$(shell cat setup.py | grep python_requires | tr -d ", '" \
		   | cut -f2- -d '=' | tr -d '>=')
PYTHON=$(shell ./scripts/find-python-version.sh $(PYTHON_VER))
VERSION=$(shell cat src/cctl/__init__.py | grep __version__ \
		| sed 's/__version__[[:space:]]\+=[[:space:]]\+//g' \
		| sed "s/'//g")

.PHONY: build manpage docs install uninstall install-docs uninstall-docs \
	test-feature test-unit test

build:
	$(PYTHON) -m build

prepare-deb:
	$(PYTHON) setup.py --command-packages=stdeb.command bdist_deb
	@echo "Please tweak the values in deb_dist/"

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
	$(PYTHON) -m pip install dist/cctl-$(VERSION)-py3-none-any.whl \
		--force-reinstall

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
