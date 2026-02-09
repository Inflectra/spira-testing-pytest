# Publishing pytest-spiratest to PyPI

## Prerequisites

Install build tools (if not already installed):
```bash
pip install --upgrade build twine
```

## Publishing Steps

### 1. Clean previous builds
```bash
rm -rf dist/ build/ *.egg-info
```

### 2. Build the package
```bash
python -m build
```

This creates:
- `dist/pytest-spiratest-2.0.2.tar.gz` (source distribution)
- `dist/pytest_spiratest-2.0.2-py3-none-any.whl` (wheel)

### 3. Check the build (optional but recommended)
```bash
twine check dist/*
```

### 4. Test upload to TestPyPI (optional but recommended)
```bash
twine upload --repository testpypi dist/*
```

You'll be prompted for your TestPyPI credentials.

### 5. Upload to PyPI (production)
```bash
twine upload dist/*
```

You'll be prompted for your PyPI credentials.

## Verification

After publishing, verify the package:
```bash
# Wait a minute for PyPI to update, then:
pip install --upgrade pytest-spiratest

# Check version
pip show pytest-spiratest
```

## Quick Reference (All Steps)

```bash
# Clean, build, and publish
rm -rf dist/ build/ *.egg-info
python -m build
twine check dist/*
twine upload dist/*
```

## Troubleshooting

### Authentication Error
If you get authentication errors, you can use API tokens:
1. Go to https://pypi.org/manage/account/token/
2. Create a new API token
3. Use `__token__` as username and the token as password

Or configure `.pypirc`:
```ini
[pypi]
username = __token__
password = pypi-YOUR-TOKEN-HERE
```

### Version Already Exists
If version 2.0.2 already exists on PyPI, you'll need to increment to 2.0.3:
1. Edit `setup.py` and change version to `2.0.3`
2. Rebuild and upload

### Package Name Conflict
If someone else owns `pytest-spiratest` on PyPI, you may need to contact PyPI support or use a different name.

## Notes

- You can only upload each version once to PyPI
- Once uploaded, you cannot delete or modify a version (only yank it)
- Always test with TestPyPI first if you're unsure
- Make sure to commit and tag your release in git:
  ```bash
  git add .
  git commit -m "Release version 2.0.2"
  git tag v2.0.2
  git push origin main --tags
  ```
