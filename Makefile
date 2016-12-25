# Makefile to ease trivial tasks for the project

VENV="$(shell find . -name ".*env")"
IN_VENV="$(shell python env.py)"
REQ=requirements.txt

.PHONY: install
install:
	# install the virtual environment
	@test -d $(VENV) && virtualenv $(VENV) || virtualenv .venv


.PHONY: clean
clean:
	# clean out cache and temporary files
	@find . \( -name "*.pyc" -o -name "output.csv" \) -type f -delete
	@find . -name "*.json" -type f -delete
	@find . -name "test_output.csv" -type f -delete
	@find . -name "__pycache__" -type d -delete


.PHONY: upgrade
upgrade:
	# upgrade PIP on virtual environment
	@test 1 -eq $(IN_VENV) && pip install -U pip && pip install -r $(REQ) \
	|| echo 'Activate virtual environment first'


.PHONY: update
update:
	# update PIP requirements
	@test 1 -eq $(IN_VENV) && pip freeze > $(REQ) \
	|| echo 'Activate virtual environment first'
