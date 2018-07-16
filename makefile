
FLAGS=

init:
	python3.6 -m venv env
	echo "To enter env, run:"
	echo "source env/bin/activate"

test:
	pytest tests

image:
	docker build -t mqtt-bridge -f mqtt-to-clientstrean.dockerfile .

clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -f `find . -type f -name '@*' `
	rm -f `find . -type f -name '#*#' `
	rm -f `find . -type f -name '*.orig' `
	rm -f `find . -type f -name '*.rej' `
	rm -f .coverage
	rm -rf coverage
	rm -rf build
	rm -rf htmlcov
	rm -rf dist
	rm -rf *.egg-info

.PHONY: init image clean test
