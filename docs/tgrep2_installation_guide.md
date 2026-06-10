# TGREP2 Binary Installation & Configuration Guide

This repository contains two refactored C-based versions of the `tgrep2` tool that have been updated to run on modern Linux systems.

## Prerequisites

To build and compile these tools from source, ensure your environment has standard build utilities:
- GCC compiler
- GNU Make

## Compilation and Installation

Both binaries can be compiled and installed using the root-level `Makefile`. Run the following command from the repository root:

```bash
make install
```

This compiles both versions of the tool and places their executables in the `bin/` directory:
1. `bin/tgrep2-bwaldon` (based on https://github.com/bwaldon/tgrep2)
2. `bin/tgrep2-andreasvc` (based on https://github.com/andreasvc/tgrep2)

## Configuring the Python Class

The `TgrepOrchestrator` class automatically looks for these binaries in the default `bin/` subdirectory relative to the script location or current working directory. 

To configure a custom path or a system-wide executable, pass the path when instantiating the orchestrator:

```python
from tgrep_orchestrator import TgrepOrchestrator

# 1. Automatic resolution (looks for bin/tgrep2-andreasvc or bin/tgrep2-bwaldon)
orchestrator = TgrepOrchestrator()

# 2. Custom path configuration (explicit path to a specific binary)
orchestrator = TgrepOrchestrator(tgrep2_binary_path="/path/to/my/tgrep2-binary")

# 3. System PATH fallback (if binary is in system PATH, e.g. /usr/local/bin/tgrep2)
orchestrator = TgrepOrchestrator(tgrep2_binary_path="tgrep2")
```
