ifdef CMD
	DOCKER_CMD=$(CMD)
else
	DOCKER_CMD=/bin/bash
endif

DOCKER_RUN_COMMAND=docker-compose -f tools/compose-config.yml run dev_pyprometheus


default: help

include tools/Makefile


#version := $(shell sh -c "egrep -oe '__version__\s+=\s+(.*)' ./pyprometheus/__init__.py | sed 's/ //g' | sed \"s/'//g\" | sed 's/__version__=//g'")

version := $(shell sh -c "$(DOCKER_RUN_COMMAND) 'python setup.py --version'")
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

help:
	@echo "Available commands:"
	@sed -n '/^[a-zA-Z0-9_.]*:/s/:.*//p' <Makefile | sort


publish: clean-pyc
	@echo "Create release $(version) and upload to pypi"
	git tag -f v$(version) && git push --tags
	$(DOCKER_RUN_COMMAND) "python setup.py sdist bdist_wheel"
	$(DOCKER_RUN_COMMAND) 'for d in dist/* ; do twine register "$$d"; done;'
	$(DOCKER_RUN_COMMAND) "twine upload dist/*"
	@echo ""

test: clean-containers
	@echo "Test application $(version)"
	$(DOCKER_RUN_COMMAND) "uwsgi --pyrun setup.py --pyargv test --sharedarea=100 --enable-threads"
	@echo ""

tox: clean-containers
	@echo "Tox test application $(version)"
	$(DOCKER_RUN_COMMAND) "tox"
	@echo ""

lint: clean-containers
	@echo "Linting python files"
	$(DOCKER_RUN_COMMAND) "PYFLAKES_NODOCTEST=1 flake8 pyprometheus" || exit 1
	@echo ""

.PHONY: test publish lint help clean-pyc tox
