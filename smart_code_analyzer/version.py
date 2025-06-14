#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------------------------------------------------
from pathlib import Path


def get_version():
    try:
        import tomli
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            pyproject = tomli.load(f)
        return pyproject["tool"]["poetry"]["version"]
    except Exception:
        return "unknown"
