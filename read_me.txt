# BridgeLab Editorial Toolkit

**Version:** 1.0.0 (Phase 1)

---

## Overview

The **BridgeLab Editorial Toolkit** is a Python application designed to maintain, validate, and analyze the BridgeLab Contract Bridge encyclopedia.

Rather than editing hundreds of Markdown files manually, the toolkit automates repetitive editorial tasks while preserving the encyclopedia's structure and consistency.

The toolkit is intended for repository maintenance and is not part of the published BridgeLab content.

---

# Current Features (Phase 1)

The toolkit currently provides the following capabilities:

* Repository scanning
* Markdown article parsing
* YAML metadata extraction
* Heading extraction
* Repository statistics
* Repository validation
* JSON export
* Command-line interface

Phase 1 establishes the technical foundation for future metadata management, cross-reference generation, glossary creation, bibliography generation, and auditing.

---

# Project Structure

```text
bridgelab-toolkit/
│
├── README.md
├── requirements.txt
├── config.py
├── main.py
│
├── core/
│   ├── models.py
│   ├── scanner.py
│   ├── parser.py
│   ├── repository.py
│   └── statistics.py
│
├── commands/
│   └── scan.py
│
├── validator/
│   ├── validator.py
│   ├── duplicate_check.py
│   ├── filename_check.py
│   ├── yaml_check.py
│   ├── heading_check.py
│   └── directory_check.py
│
├── output/
├── reports/
└── tests/
```

---

# Installation

Install the required Python packages:

```bash
pip install -r requirements.txt
```

---

# Running the Toolkit

Scan the BridgeLab repository:

```bash
python main.py scan
```

Validate repository structure and article metadata without modifying source files:

```bash
python main.py validate
```

Both commands accept `--root PATH` to target a repository explicitly. The
validation command exits with status `1` when errors are found and status `0`
for a clean or warnings-only result, making it suitable for CI checks.

The toolkit automatically locates the BridgeLab root directory using the configuration in `config.py`.

---

# Output

After a successful scan, the toolkit generates:

```text
output/

articles.json
statistics.json
statistics.txt
validation.json
validation.txt
```

These files are regenerated whenever the toolkit runs.

---

# Repository Model

Every Markdown article is represented internally as an `Article` object.

Each object contains:

* article identifier
* filename
* path
* metadata
* headings
* statistics
* links
* validation information

This internal model is used by all toolkit components.

---

# Validation

The validator currently checks:

* duplicate filenames
* filename conventions
* required YAML metadata
* required headings
* directory organization

Additional validation rules will be added in later phases.

---

# Statistics

The statistics engine reports:

* number of articles
* total words
* total lines
* repository size
* category counts
* subcategory counts
* heading frequencies

---

# Configuration

Global settings are defined in:

```text
config.py
```

This includes:

* repository location
* output directories
* required metadata
* required headings
* ignored directories

---

# Requirements

The toolkit currently depends on:

* Python 3.12+
* Typer
* Rich
* PyYAML

---

# Development Roadmap

## Phase 1 — Repository Foundation ✅

* Repository scanner
* Parser
* Statistics engine
* Validator
* CLI
* Configuration

## Phase 2 — Metadata Engine

* Metadata validation
* Metadata repair
* YAML generation
* Metadata reports

## Phase 3 — Cross-Reference Engine

* Automatic cross-reference generation
* Link validation
* Relationship graph

## Phase 4 — Encyclopedia Generators

* Glossary
* Acronyms
* Bibliography
* Topic index

## Phase 5 — Repository Audit

* Duplicate detection
* Consistency analysis
* Structural reports
* Editorial quality checks

## Phase 6 — Build System

Complete repository build and maintenance from a single command.

---

# Design Principles

The toolkit follows several core principles:

* One responsibility per module.
* No duplicated logic.
* Configuration separated from implementation.
* Reusable data models.
* Modular architecture.
* Automation where possible.
* Human editorial review where required.

---

# License

This toolkit is developed exclusively for the maintenance of the BridgeLab encyclopedia.

python main.py scan

python main.py validate

python main.py metadata

python main.py crossrefs

python main.py glossary

python main.py acronyms

python main.py bibliography

python main.py build
