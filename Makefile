.PHONY: black-check black-reformat build clean flake8 gh-pages install \
	isort-check isort-reformat mypy pytest reformat release lint test

black-check:
	black --check --diff .

black-reformat:
	black .

build:
	python setup.py sdist

clean:
	find . -name '*.pyc' -delete
	rm -rf __pycache__ *.egg-info .cache .tox build dist htmlcov prof

flake_ignore = --ignore=E203,E266,E501,W503
flake_options = --isolated --max-line-length=88

flake8:
	flake8 ${flake_ignore} ${flake_options}

gh-pages:
	rm -rf gh-pages/
	git clone --depth=1 https://github.com/Abjad/rmakers.git gh-pages
	cd gh-pages && \
	if git checkout gh-pages; then \
	    echo "Using existing gh-pages branch"; \
	else \
	    git checkout --orphan gh-pages && git rm -rf .; \
	fi
	rsync -rtv --delete --exclude=.git docs/build/html/ gh-pages/
	cd gh-pages && touch .nojekyll && \
		git add --all . && \
		git commit --allow-empty -m "Update docs" && \
		git push --force origin gh-pages
	rm -rf gh-pages/

isort-check:
	isort --case-sensitive --check-only --line-width=88 --multi-line=3 \
		  --project=rmakers --thirdparty=abjad --thirdparty=baca \
		  --thirdparty=ply --thirdparty=uqbar --trailing-comma --use-parentheses .

isort-reformat:
	isort --case-sensitive --line-width=88 --multi-line=3 \
	      --project=rmakers --thirdparty=abjad --thirdparty=baca \
		  --thirdparty=ply --thirdparty=uqbar --trailing-comma --use-parentheses .

mypy:
	mypy source

pytest:
	pytest .

reformat: black-reformat isort-reformat

release:
	make clean
	make build
	twine upload dist/*.tar.gz

lint: black-check flake8 isort-check mypy

test: lint pytest
