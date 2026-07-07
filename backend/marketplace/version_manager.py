"""Semantic versioning comparator and constraint matching manager."""

import re
from typing import List, Tuple


class VersionManager:
    """Manages version comparisons and constraint parsing for packages."""

    @staticmethod
    def parse_version(version_str: str) -> Tuple[int, int, int]:
        """Parses a version string 'X.Y.Z' into a tuple of integers."""
        parts = version_str.strip().split(".")
        major = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 0
        minor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        patch = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
        return major, minor, patch

    @classmethod
    def compare_versions(cls, v1: str, v2: str) -> int:
        """Compares two versions. Returns -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2."""
        t1 = cls.parse_version(v1)
        t2 = cls.parse_version(v2)
        if t1 < t2:
            return -1
        elif t1 > t2:
            return 1
        return 0

    @classmethod
    def matches_constraint(cls, version: str, constraint: str) -> bool:
        """Evaluates a version against a constraint string (e.g. '>=1.0.0', '<2.0.0')."""
        constraint = constraint.strip()
        if not constraint or constraint == "*":
            return True

        # Handle operators
        match = re.match(r"^([>=<!~^]+)\s*(.*)$", constraint)
        if not match:
            # Assume exact match if no operator is specified
            return cls.compare_versions(version, constraint) == 0

        operator, target_ver = match.groups()
        comp = cls.compare_versions(version, target_ver)

        if operator == "==":
            return comp == 0
        elif operator == "!=":
            return comp != 0
        elif operator == ">=":
            return comp >= 0
        elif operator == "<=":
            return comp <= 0
        elif operator == ">":
            return comp > 0
        elif operator == "<":
            return comp < 0
        elif operator == "~" or operator == "~=":
            # Compatible release: must share major and minor version numbers
            v_maj, v_min, _ = cls.parse_version(version)
            t_maj, t_min, _ = cls.parse_version(target_ver)
            return v_maj == t_maj and v_min == t_min and comp >= 0
        elif operator == "^":
            # Caret requirement: allows changes that do not modify the left-most non-zero digit
            v_maj, v_min, v_pat = cls.parse_version(version)
            t_maj, t_min, t_pat = cls.parse_version(target_ver)
            if t_maj > 0:
                return v_maj == t_maj and comp >= 0
            elif t_min > 0:
                return v_maj == 0 and v_min == t_min and comp >= 0
            else:
                return v_maj == 0 and v_min == 0 and v_pat == t_pat

        return False
        
    @classmethod
    def matches_all_constraints(cls, version: str, constraints_str: str) -> bool:
        """Splits comma-separated constraints and verifies if version satisfies all."""
        parts = [p.strip() for p in constraints_str.split(",") if p.strip()]
        return all(cls.matches_constraint(version, p) for p in parts)
