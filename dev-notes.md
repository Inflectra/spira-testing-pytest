# How to setup and distribute plugin

## Environment setup
- install python 3+
- install pip
- update pip as required
- install pytest `pip install pytest`
- install twine for distribution `pip install twine`

## Work and test code locally
- change version number in setup.py
- to build locally and replace the local package run `pip install -e ./`
- you can then access the package as you would normally. So in your test setup run `pytest sample_test.py` and it will use this local plugin
- make changes to code, repeat building and testing locally 

## Distribute code
- double check the version is correct in setup.py
- delete any files in the dist folder
- run `python -m pip install --upgrade build`
- run `python -m build`
- run `python -m twine upload dist/*`
- at the prompt for the username type __TOKEN__
- for the password paste the API key that is stored with the login information for https://pypi.org/
- if the above credentials do not work you can try the standard username and password for https://pypi.org/

# Useful links
https://packaging.python.org/tutorials/packaging-projects/