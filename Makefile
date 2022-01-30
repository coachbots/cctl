build:
	python3 -m build

install:
	python3 -m pip install dist/cctl-*.whl

uninstall:
	python3 -m pip uninstall cctl
