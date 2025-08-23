# AGENTS.md

This document identifies and describes all agent and agent-like components in the [Lightning-AI/utilities](https://github.com/Lightning-AI/utilities) repository. Agents are defined as independently-triggerable components responsible for automating tasks, orchestrating workflows, or executing delegated utility operations. For each agent, its **name**, **purpose**, **functionality**, and **relative file location** are given.

______________________________________________________________________

## 1. GitHub Workflow Agents

### Agent: check-schema

- **Purpose**: Validates configuration or data schema on code pushes.
- **Functionality**: Automatically runs schema checks as a job for every push, using centralized logic.
- **Relative Location**: `.github/workflows/check-schema.yml`

### Agent: check-code

- **Purpose**: Ensures code quality and standards compliance before merging or release.
- **Functionality**: Runs code style, lint, and other static analysis checks.
- **Relative Location**: `.github/workflows/check-code.yml`

### Agent: ci-use-checks

- **Purpose**: Coordinates schema and code validation jobs for broad CI coverage.
- **Functionality**: Calls multiple reusable workflows; acts as a top-level CI orchestrator.
- **Relative Location**: `.github/workflows/ci-use-checks.yaml`

### Agent: cron-clear-cache

- **Purpose**: Maintains clean build environments by scheduled cache clearance.
- **Functionality**: Invokes Python/environment cache clearing on a weekly schedule to keep CI fast.
- **Relative Location**: `.github/workflows/cron-clear-cache.yml`

______________________________________________________________________

## 2. GitHub Composite Actions

### Agent: cache

- **Purpose**: Facilitates caching of Python dependencies and environments.
- **Functionality**: Stores and restores pip/wheel caches, reducing CI overhead and redundant downloads.
- **Relative Location**: `.github/actions/cache`

### Agent: setup-python (in workflows)

- **Purpose**: Sets up specified Python version for CI jobs.
- **Functionality**: Ensures a clean Python install with exact version matching workflow needs.
- **Relative Location**: Referenced in `.github/workflows/*.yml`

______________________________________________________________________

## 3. CLI Utility Agents

### Agent: lightning_utilities.cli.requirements

- **Purpose**: Automates manipulation of requirements files for testing compatibility.
- **Functionality**: CLI group for managing and editing dependency specification (e.g., pinning constraints).
- **Relative Location**: `src/lightning_utilities/cli/requirements.py`

### Agent: lightning_utilities.cli.run

- **Purpose**: Provides entry point for executing Python scripts.
- **Functionality**: Runs user-specified scripts/modules with logging and reproducibility enhancements.
- **Relative Location**: `src/lightning_utilities/cli/run.py`

### Agent: lightning_utilities.cli.install

- **Purpose**: Automates Python dependency installation.
- **Functionality**: CLI agent for installing required packages with optional command-line constraints or options.
- **Relative Location**: `src/lightning_utilities/cli/install.py`

### Agent: lightning_utilities.cli.console

- **Purpose**: Manages output, error, and logging for CLI commands.
- **Functionality**: Formats and routes output, controls verbosity, and ensures consistent messaging.
- **Relative Location**: `src/lightning_utilities/cli/console.py`

### Agent: lightning_utilities.cli.run_app

- **Purpose**: Launches application modules through the CLI.
- **Functionality**: Orchestrates app startup and configuration via command-line interface.
- **Relative Location**: `src/lightning_utilities/cli/run_app.py`

______________________________________________________________________

## 4. Core Python Utility Agents

### Agent: module_available (from core.imports)

- **Purpose**: Checks runtime availability of a named module or package.
- **Functionality**: Returns Boolean status for importability; supports conditional execution patterns.
- **Relative Location**: `src/lightning_utilities/core/imports.py`

### Agent: RequirementCache

- **Purpose**: Encapsulates package requirement availability and version checks.
- **Functionality**: Determines if current environment meets module/package specs, with diagnostics.
- **Relative Location**: `src/lightning_utilities/core/imports.py`

### Agent: LazyModule

- **Purpose**: Defers import of a Python module until actually accessed.
- **Functionality**: Creates a proxy agent for cost-saving, lazy import pattern on first attribute look-up.
- **Relative Location**: `src/lightning_utilities/core/imports.py`

### Agent: requires (decorator)

- **Purpose**: Ensures that decorated routines only execute if required modules/packages are present.
- **Functionality**: Throws warning or error if preconditions not met, halting execution.
- **Relative Location**: `src/lightning_utilities/core/imports.py`

### Agent: apply_func

- **Purpose**: Applies a function recursively to all items within complex/nested data collections.
- **Functionality**: Recursively transforms dicts, lists, tuples with a callable, supporting agent-style iteration.
- **Relative Location**: `src/lightning_utilities/core/apply_func.py`

### Agent: packaging

- **Purpose**: Parses, verifies and resolves package metadata and versions.
- **Functionality**: Provides robust version and compatibility checking for automation and CI tasks.
- **Relative Location**: `src/lightning_utilities/core/packaging.py`

______________________________________________________________________

## 5. Agent-like Scripts

### Agent: install.sh

- **Purpose**: Automates environment setup and dependency installation.
- **Functionality**: Executable shell script for batch installations, often called in setup routines.
- **Relative Location**: `scripts/install.sh`

### Agent: (other scripts)

- **Purpose**: (Varies) May provide changelog, release, or status automation.
- **Functionality**: Targeted agents for specialized project tasks.
- **Relative Location**: `scripts/` (per script)

______________________________________________________________________

## 6. Orchestration and Decision Agents

### Agent pattern: Declarative workflow orchestration

- **Purpose**: Enables CI jobs and composite actions to trigger, communicate, and conditionally execute based on context or outputs.
- **Functionality**: Uses matrix, outputs, and conditional logic in YAML to link agent logic across jobs.
- **Relative Location**: `.github/workflows/*.yml` (see usage of `needs`, `if`, `with`, outputs)

### Agent pattern: Enum/decisionflow agents

- **Purpose**: Encodes execution paths and decisions for agents.
- **Functionality**: Provides enumerated constants used throughout automation logic.
- **Relative Location**: `src/lightning_utilities/core/enums.py`

______________________________________________________________________

## AGENTS.md Conventions

- Document each agent by **name**, **purpose**, **functionality**, and **location**.
- Use flat Markdown headings for agent categories and individual agents.
- Reference file locations relative to repository root.
- Update and expand this file as new agents, utilities, CLI commands, or automation scripts are introduced.
- Align all documentation with [standard AGENTS.md conventions](https://github.com/openai/agents.md), [Agent Rules](https://agent-rules.org/), and [modern markdown guidelines](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax).
- Keep instructions clear, explicit, and brief for both human collaborators and machine/agent consumers.

______________________________________________________________________
