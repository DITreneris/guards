#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Version Bumping Script for Guards & Robbers Project

This script automates the process of updating version numbers across
multiple project files to ensure consistency. It supports semantic
versioning (MAJOR.MINOR.PATCH) updates and can be configured to target
specific files.

Usage:
    python bump_version.py --type [major|minor|patch] [--dry-run]
    python bump_version.py --set-version X.Y.Z [--dry-run]
"""

import os
import re
import sys
import json
import argparse
import datetime
from typing import Dict, List, Optional, Tuple, Union


class VersionBumper:
    """Handles version bumping across project files."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.workspace_dir = os.path.dirname(os.path.abspath(__file__))
        self.today = datetime.datetime.now().strftime("%Y-%m-%d")
        self.today_formatted = datetime.datetime.now().strftime("%B %d, %Y")
        
        # Configuration for which files to update and how
        self.config = self._load_config()
        
        # Track files that were modified
        self.modified_files = []

    def _load_config(self) -> Dict:
        """Load version bumping configuration."""
        # Default configuration if no config file exists
        default_config = {
            "version_files": [
                {
                    "file": "README.md",
                    "patterns": [
                        {
                            "search": r"\*Version: (\d+\.\d+\.\d+)\*",
                            "replace": "*Version: {new_version}*"
                        },
                        {
                            "search": r"\*Last updated: ([^*]+)\*",
                            "replace": "*Last updated: {date_formatted}*"
                        }
                    ]
                },
                {
                    "file": "dev_plan.md",
                    "patterns": [
                        {
                            "search": r"\*Version: (\d+\.\d+\.\d+)\*",
                            "replace": "*Version: {new_version}*"
                        },
                        {
                            "search": r"\*Last updated: ([^*]+)\*",
                            "replace": "*Last updated: {date_formatted}*"
                        }
                    ]
                },
                {
                    "file": "version_management.md",
                    "patterns": [
                        {
                            "search": r"\*Version: (\d+\.\d+\.\d+)\*",
                            "replace": "*Version: {new_version}*"
                        }
                    ]
                },
                {
                    "file": "static/js/script.js",
                    "patterns": [
                        {
                            "search": r"const APP_VERSION = ['\"](\d+\.\d+\.\d+)['\"];",
                            "replace": "const APP_VERSION = \"{new_version}\";"
                        }
                    ]
                }
            ],
            "version_registry": "version_registry.json"
        }
        
        # Try to load config from file, use default if not found
        config_path = os.path.join(self.workspace_dir, "version_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config file: {e}")
                print("Using default configuration")
                return default_config
        else:
            return default_config

    def get_current_version(self) -> str:
        """
        Get current version from the version registry or README.md.
        Returns: Current semantic version string (e.g., "1.2.0")
        """
        # Try to get version from registry first
        registry_path = os.path.join(self.workspace_dir, self.config.get("version_registry"))
        if os.path.exists(registry_path):
            try:
                with open(registry_path, 'r') as f:
                    registry = json.load(f)
                    return registry.get("latest", "0.0.0")
            except (json.JSONDecodeError, IOError):
                pass
        
        # Fall back to README.md
        readme_path = os.path.join(self.workspace_dir, "README.md")
        if os.path.exists(readme_path):
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
                version_match = re.search(r'\*Version: (\d+\.\d+\.\d+)\*', content)
                if version_match:
                    return version_match.group(1)
        
        # Default if no version found
        return "0.0.0"

    def parse_version(self, version_str: str) -> Tuple[int, int, int]:
        """Parse a version string into its components."""
        match = re.match(r'^(\d+)\.(\d+)\.(\d+)$', version_str)
        if not match:
            raise ValueError(f"Invalid version format: {version_str}")
        
        major, minor, patch = match.groups()
        return int(major), int(minor), int(patch)

    def bump_version(self, current_version: str, bump_type: str) -> str:
        """
        Bump the version according to semantic versioning.
        
        Args:
            current_version: Current version string
            bump_type: 'major', 'minor', or 'patch'
            
        Returns:
            New version string
        """
        major, minor, patch = self.parse_version(current_version)
        
        if bump_type == 'major':
            return f"{major + 1}.0.0"
        elif bump_type == 'minor':
            return f"{major}.{minor + 1}.0"
        elif bump_type == 'patch':
            return f"{major}.{minor}.{patch + 1}"
        else:
            raise ValueError(f"Invalid bump type: {bump_type}")

    def update_file_version(self, file_path: str, patterns: List[Dict], new_version: str) -> bool:
        """
        Update version in a single file based on patterns.
        
        Args:
            file_path: Path to the file
            patterns: List of search/replace patterns
            new_version: New version string
            
        Returns:
            True if file was modified, False otherwise
        """
        if not os.path.exists(file_path):
            print(f"Warning: File {file_path} does not exist, skipping")
            return False
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        for pattern in patterns:
            search = pattern['search']
            replace_template = pattern['replace']
            
            # Format the replacement string
            replace = replace_template.format(
                new_version=new_version,
                date=self.today,
                date_formatted=self.today_formatted
            )
            
            # Apply the replacement
            content = re.sub(search, replace, content)
        
        # Check if content was modified
        if content != original_content:
            if not self.dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Updated version in {file_path}")
            else:
                print(f"[DRY RUN] Would update version in {file_path}")
            return True
        else:
            print(f"No version pattern matched in {file_path}")
            return False

    def update_version_registry(self, new_version: str, commit_hash: Optional[str] = None) -> None:
        """
        Update the version registry JSON file with the new version.
        
        Args:
            new_version: The new version string
            commit_hash: Optional Git commit hash for the release
        """
        registry_path = os.path.join(self.workspace_dir, self.config.get("version_registry"))
        
        # Initialize registry if it doesn't exist
        if not os.path.exists(registry_path):
            registry = {
                "latest": new_version,
                "releases": []
            }
        else:
            try:
                with open(registry_path, 'r') as f:
                    registry = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error reading version registry: {e}")
                registry = {
                    "latest": new_version,
                    "releases": []
                }
        
        # Update latest version
        registry["latest"] = new_version
        
        # Add new release entry if it doesn't exist
        release_exists = False
        for release in registry.get("releases", []):
            if release.get("version") == new_version:
                release_exists = True
                release["date"] = self.today
                if commit_hash:
                    release["commit"] = commit_hash
                break
        
        if not release_exists:
            # Create a new release entry
            new_release = {
                "version": new_version,
                "date": self.today,
                "highlights": [],
                "documents": []
            }
            
            if commit_hash:
                new_release["commit"] = commit_hash
                
            # Add document versions
            for file_config in self.config.get("version_files", []):
                file_name = file_config.get("file")
                if file_name and file_name.endswith(".md"):
                    base_name = os.path.basename(file_name)
                    new_release["documents"].append({
                        "name": base_name,
                        "version": new_version
                    })
            
            # Insert at the beginning of the releases array
            registry.setdefault("releases", []).insert(0, new_release)
        
        # Write updated registry
        if not self.dry_run:
            with open(registry_path, 'w', encoding='utf-8') as f:
                json.dump(registry, f, indent=2)
            print(f"Updated version registry in {registry_path}")
        else:
            print(f"[DRY RUN] Would update version registry in {registry_path}")

    def update_all_files(self, new_version: str) -> List[str]:
        """
        Update version in all configured files.
        
        Args:
            new_version: New version string
            
        Returns:
            List of modified files
        """
        modified = []
        
        for file_config in self.config.get("version_files", []):
            file_path = os.path.join(self.workspace_dir, file_config.get("file"))
            patterns = file_config.get("patterns", [])
            
            if self.update_file_version(file_path, patterns, new_version):
                modified.append(file_path)
        
        # Update version registry
        if not self.dry_run:
            self.update_version_registry(new_version)
        
        return modified

    def run(self, bump_type: Optional[str] = None, set_version: Optional[str] = None) -> List[str]:
        """
        Run the version bumping process.
        
        Args:
            bump_type: Type of bump ('major', 'minor', 'patch') or None
            set_version: Specific version to set or None
            
        Returns:
            List of modified files
        """
        current_version = self.get_current_version()
        print(f"Current version: {current_version}")
        
        if set_version:
            # Validate format of set_version
            try:
                self.parse_version(set_version)
                new_version = set_version
                print(f"Setting version to: {new_version}")
            except ValueError as e:
                print(f"Error: {e}")
                return []
        elif bump_type:
            # Bump version according to type
            new_version = self.bump_version(current_version, bump_type)
            print(f"Bumping {bump_type} version to: {new_version}")
        else:
            print("Error: Either bump_type or set_version must be specified")
            return []
        
        # Update files
        modified_files = self.update_all_files(new_version)
        
        # Summary
        if self.dry_run:
            print("\n[DRY RUN] Summary:")
            print(f"  Would bump version from {current_version} to {new_version}")
            print(f"  Would modify {len(modified_files)} files")
        else:
            print("\nSummary:")
            print(f"  Bumped version from {current_version} to {new_version}")
            print(f"  Modified {len(modified_files)} files")
        
        return modified_files


def main() -> int:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Bump version numbers across project files")
    
    version_group = parser.add_mutually_exclusive_group(required=True)
    version_group.add_argument(
        "--type", "-t", 
        choices=["major", "minor", "patch"],
        help="Type of version bump to perform"
    )
    version_group.add_argument(
        "--set-version", "-s",
        help="Set to a specific version (format: X.Y.Z)"
    )
    
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Display changes without modifying files"
    )
    
    parser.add_argument(
        "--commit", "-c",
        action="store_true",
        help="Commit changes to git after bumping version"
    )
    
    args = parser.parse_args()
    
    try:
        bumper = VersionBumper(dry_run=args.dry_run)
        modified_files = bumper.run(
            bump_type=args.type,
            set_version=args.set_version
        )
        
        # Optionally commit changes to git
        if args.commit and modified_files and not args.dry_run:
            new_version = bumper.get_current_version()
            
            try:
                import subprocess
                
                # Add modified files
                subprocess.run(["git", "add"] + modified_files, check=True)
                
                # Add version registry if it exists
                registry_path = os.path.join(bumper.workspace_dir, bumper.config.get("version_registry"))
                if os.path.exists(registry_path):
                    subprocess.run(["git", "add", registry_path], check=True)
                
                # Create commit
                commit_message = f"Bump version to {new_version}"
                subprocess.run(["git", "commit", "-m", commit_message], check=True)
                
                print(f"\nCommitted version bump to git with message: '{commit_message}'")
                
            except subprocess.CalledProcessError as e:
                print(f"Error committing to git: {e}")
                return 1
            except ImportError:
                print("Could not import subprocess module, skipping git commit")
        
        return 0
    
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 