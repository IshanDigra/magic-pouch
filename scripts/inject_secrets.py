#!/usr/bin/env python3
"""
Enterprise Secret Injection Module

This module provides a robust, production-grade mechanism for injecting
configuration values and secrets into frontend static files during the
CI/CD build process.

Key Features:
  - No shell escaping required (eliminates sed/envsubst fragility)
  - Atomic file operations (prevents partial writes)
  - Comprehensive error handling and reporting
  - UTF-8 Unicode support for international characters
  - Non-destructive placeholder targeting (preserves non-target content)
  - Detailed audit trail for compliance and debugging

Theoretical Justification:
  Traditional shell tools (sed, envsubst) fail when secrets contain
  special characters (/, \, $, ", '). This script treats the file
  content as a string object, eliminating character interpretation issues.

Usage:
  python3 scripts/inject_secrets.py

Author: DevOps Engineering Team
License: MIT
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Tuple


class SecretInjectionError(Exception):
    """Base exception for secret injection failures."""
    pass


class SecretInjector:
    """
    Handles secure injection of environment variables into configuration files.

    This class provides:
    - Atomic file operations (write to temp, then rename)
    - Detailed audit logging
    - Comprehensive error handling
    - Support for multiple target files
    """

    def __init__(self, verbose: bool = True):
        """
        Initialize the SecretInjector.

        Args:
            verbose (bool): Enable detailed logging output.
        """
        self.verbose = verbose
        self.replacements_made = 0
        self.warnings = []
        self.errors = []

    def log(self, message: str, level: str = "INFO") -> None:
        """
        Log a message with timestamp and level.

        Args:
            message (str): The message to log.
            level (str): Log level (INFO, WARNING, ERROR, SUCCESS).
        """
        if not self.verbose and level not in ["ERROR", "WARNING"]:
            return

        level_symbols = {
            "INFO": "[i]",
            "SUCCESS": "✓",
            "WARNING": "⚠",
            "ERROR": "✗",
        }
        symbol = level_symbols.get(level, "[*]")
        print(f"{symbol} {level}: {message}")

    def inject_file(self, file_path: str, token_map: Dict[str, str]) -> Tuple[bool, int]:
        """
        Inject secrets into a single file.

        This method:
        1. Validates that the file exists
        2. Reads the file with UTF-8 encoding
        3. Replaces placeholders with environment variable values
        4. Atomically writes the result using a temporary file
        5. Validates the operation succeeded

        Args:
            file_path (str): Path to the target file.
            token_map (Dict[str, str]): Mapping of placeholders to env var names.
                Example: {"__API_KEY__": "SECRET_API_KEY"}

        Returns:
            Tuple[bool, int]: (success, number_of_replacements_made)

        Raises:
            SecretInjectionError: On file I/O or injection failure.
        """
        abs_path = Path(file_path).resolve()

        # Phase 1: Validation
        if not abs_path.exists():
            raise SecretInjectionError(
                f"Target file does not exist: {abs_path}"
            )

        if not abs_path.is_file():
            raise SecretInjectionError(
                f"Target path is not a file: {abs_path}"
            )

        self.log(f"Processing file: {abs_path}")

        # Phase 2: Read file
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                original_content = f.read()
            self.log(f"File read successfully ({len(original_content)} bytes)")
        except Exception as e:
            raise SecretInjectionError(f"Failed to read file: {e}")

        # Phase 3: Inject secrets
        modified_content = original_content
        local_replacements = 0

        for placeholder, env_var_name in token_map.items():
            secret_value = os.environ.get(env_var_name)

            if secret_value is None:
                msg = (
                    f"Skipping '{placeholder}': Environment variable "
                    f"'{env_var_name}' not set"
                )
                self.log(msg, "WARNING")
                self.warnings.append(msg)
                continue

            if placeholder in modified_content:
                modified_content = modified_content.replace(
                    placeholder, secret_value
                )
                self.log(
                    f"Replaced '{placeholder}' with value from '{env_var_name}'",
                    "SUCCESS",
                )
                local_replacements += 1
            else:
                msg = f"Placeholder '{placeholder}' not found in file"
                self.log(msg, "WARNING")
                self.warnings.append(msg)

        # Phase 4: Atomic write (using temporary file)
        try:
            # Create temporary file in same directory for atomic rename
            temp_fd, temp_path = tempfile.mkstemp(
                dir=abs_path.parent,
                prefix=".inject_",
                suffix=".tmp",
            )

            try:
                with os.fdopen(temp_fd, "w", encoding="utf-8") as temp_file:
                    temp_file.write(modified_content)

                # Atomic rename
                shutil.move(temp_path, abs_path)
                self.log(
                    f"File updated atomically ({local_replacements} secrets injected)",
                    "SUCCESS",
                )
            except Exception as e:
                # Clean up temp file on error
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise e

        except Exception as e:
            raise SecretInjectionError(f"Failed to write file: {e}")

        self.replacements_made += local_replacements
        return True, local_replacements

    def validate_secrets(self, token_map: Dict[str, str]) -> bool:
        """
        Validate that all required secrets are available in the environment.

        Args:
            token_map (Dict[str, str]): Mapping of placeholders to env var names.

        Returns:
            bool: True if all secrets are available.

        Raises:
            SecretInjectionError: If critical secrets are missing.
        """
        self.log("Validating secrets...")
        missing_secrets = []

        for placeholder, env_var_name in token_map.items():
            if env_var_name not in os.environ:
                missing_secrets.append((placeholder, env_var_name))

        if missing_secrets:
            msg = f"Missing environment variables: {[var for _, var in missing_secrets]}"
            self.log(msg, "ERROR")
            raise SecretInjectionError(msg)

        self.log(f"All {len(token_map)} secrets are present", "SUCCESS")
        return True

    def report(self) -> None:
        """Print a summary report of the injection operation."""
        print("\n" + "=" * 70)
        print("SECRET INJECTION REPORT")
        print("=" * 70)
        print(f"Total Replacements Made: {self.replacements_made}")
        print(f"Warnings: {len(self.warnings)}")
        print(f"Errors: {len(self.errors)}")

        if self.warnings:
            print("\nWarnings:")
            for warning in self.warnings:
                print(f"  - {warning}")

        if self.errors:
            print("\nErrors:")
            for error in self.errors:
                print(f"  - {error}")

        print("=" * 70 + "\n")


def main() -> int:
    """
    Main entry point for the secret injection script.

    Configuration:
    - TARGET_FILES: List of (file_path, token_map) tuples
    - Each token_map maps placeholders to environment variable names

    Environment Variables Expected:
    - FIREBASE_API_KEY: Firebase API key
    - FIREBASE_AUTH_DOMAIN: Firebase authentication domain
    - FIREBASE_PROJECT_ID: Firebase project ID
    - FIREBASE_STORAGE_BUCKET: Firebase storage bucket
    - FIREBASE_MESSAGING_SENDER_ID: Firebase messaging sender ID
    - FIREBASE_APP_ID: Firebase app ID

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    print("\n" + "=" * 70)
    print("ENTERPRISE SECRET INJECTION SYSTEM")
    print("=" * 70)
    print(f"Python Version: {sys.version.split()[0]}")
    print(f"Working Directory: {os.getcwd()}")
    print("=" * 70 + "\n")

    injector = SecretInjector(verbose=True)

    # Configuration: Files to inject and their token mappings
    TARGET_FILES = [
        (
            "config.json",
            {
                "__FIREBASE_API_KEY__": "FIREBASE_API_KEY",
                "__FIREBASE_AUTH_DOMAIN__": "FIREBASE_AUTH_DOMAIN",
                "__FIREBASE_PROJECT_ID__": "FIREBASE_PROJECT_ID",
                "__FIREBASE_STORAGE_BUCKET__": "FIREBASE_STORAGE_BUCKET",
                "__FIREBASE_MESSAGING_SENDER_ID__": "FIREBASE_MESSAGING_SENDER_ID",
                "__FIREBASE_APP_ID__": "FIREBASE_APP_ID",
            },
        ),
        (
            "index.html",
            {
                "__FIREBASE_CONFIG_JSON__": "FIREBASE_CONFIG_JSON",
            },
        ),
    ]

    try:
        # Validate all secrets are available
        all_tokens = {}
        for _, token_map in TARGET_FILES:
            all_tokens.update(token_map)
        # Note: Validation is optional; injection will skip missing vars

        # Process each file
        for file_path, token_map in TARGET_FILES:
            try:
                success, count = injector.inject_file(file_path, token_map)
                if success:
                    print()
            except SecretInjectionError as e:
                injector.errors.append(str(e))
                injector.log(str(e), "ERROR")
                # Continue processing other files
                print()

        # Print summary report
        injector.report()

        # Exit with appropriate code
        if injector.errors:
            print("INJECTION FAILED: Critical errors occurred\n")
            return 1
        else:
            print("INJECTION SUCCESSFUL: All operations completed\n")
            return 0

    except Exception as e:
        print(f"\nFATAL ERROR: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
