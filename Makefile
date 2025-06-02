.PHONY: docs
init:
	python3 -m pip install -r requirements-dev.txt

publish-test:
	python3 -m build
	python3 -m twine upload --repository mistmcp-testpypi dist/* 
	rm -fr build dist

publish:
	rm -fr build dist 
	python3 -m build
	python3 -m twine upload --repository mistmcp dist/* 
