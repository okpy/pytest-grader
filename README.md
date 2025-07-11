# pytest-grader

A pytest plugin for testing and scoring programming assignments.

## Features

- **Assignment Scoring**
  - Add point values to test functions using the `@points(n)` decorator
  - Show a score summary when running `pytest --score`
- **Test Locking** as described in Basu et al., *Automated Problem Clarification at Scale* ([abstract](https://dl.acm.org/doi/10.1145/2724660.2724679) [pdf](http://denero.org/content/pubs/las15_basu_unlocking.pdf))
  - Lock doctests using the `@lock` decorator.
  - `python3 pytest-grader --lock [src] [dest]` will generate a copy of src with doctests locked.
  - `pytest --unlock` provides an interactive interface for unlocking locked doctests.
- **Progress Logging**
  - Snapshots of assignment files, test case results, and unlocking attempts are stored in a `grader.sqlite`.
  - This file is designed to be submitted along with the assignment as a record of how the assignment was completed.
- **Coming soon: AI assistance**

## Usage

The recommended way to use this pytest plugin is to include `pytest-grader` (**Link coming soon**) in the distribution of your assignment.

**Coming soon:** It is also possible to install this with:

```bash
pip install pytest-grader
```

Also include a `conftest.py` file in the distribution of your assignment that contains `pytest_plugins = ["pytest_grader"]`.

See the `examples` directory for more usage info.

## License

A permissive license will be chosen shortly...