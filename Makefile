build:
	python3 -m build

manpage:
	mkdir -p build
	pandoc docs/cctl.1.md -s -t man -o build/cctl.1
	gzip -f build/cctl.1
	mkdir -p dist/
	mv build/cctl.1.gz dist/cctl.1.gz
	rm -r build

install:
	python3 -m pip install dist/cctl-*.whl
	mkdir -p /usr/local/man/man1
	cp dist/cctl.1.gz /usr/local/man/man1/cctl.1.gz

uninstall:
	python3 -m pip uninstall cctl
