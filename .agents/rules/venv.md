# Python Virtual Environment Requirement

You **MUST** activate and run the virtual environment located at `~/.virtualenvs/ted-data` before executing any Python scripts, commands, or tests within this workspace.

## Instructions
- To activate the virtualenv:
  ```bash
  source ~/.virtualenvs/ted-data/bin/activate
  ```
- Or execute using the virtual environment's executables directly:
  ```bash
  ~/.virtualenvs/ted-data/bin/python <script_name>.py
  ~/.virtualenvs/ted-data/bin/pytest
  ```

## Package Dependencies Installation
When setting up or updating the virtual environment, you **MUST** install the following packages from their specific Git repositories rather than PyPI:
- **benepar**: Install from source repository:
  ```bash
  pip install git+https://github.com/drewvid/self-attentive-parser.git
  ```
- **pytorch-struct**: Install from source repository:
  ```bash
  pip install git+https://github.com/harvardnlp/pytorch-struct.git
  ```

