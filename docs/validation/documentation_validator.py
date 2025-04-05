#!/usr/bin/env python3
"""
Documentation Validator
Version: 1.0.0
Last Updated: May 16, 2025
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"

@dataclass
class ValidationResult:
    level: ValidationLevel
    message: str
    file: str
    line: Optional[int] = None

class DocumentationValidator:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.templates_dir = self.root_dir / "templates"
        self.validation_rules = self._load_validation_rules()
        
    def _load_validation_rules(self) -> Dict:
        """Load validation rules from YAML file."""
        rules_file = self.root_dir / "validation" / "rules.yaml"
        if rules_file.exists():
            with open(rules_file, 'r') as f:
                return yaml.safe_load(f)
        return {
            "required_sections": [
                "Overview",
                "Table of Contents",
                "Change Log",
                "Contact"
            ],
            "required_metadata": [
                "Version",
                "Last Updated",
                "Document Owner",
                "Access Level"
            ],
            "markdown_standards": {
                "max_line_length": 100,
                "heading_levels": ["#", "##", "###", "####"],
                "code_block_languages": ["python", "bash", "json", "yaml", "markdown"]
            }
        }

    def validate_documentation(self) -> List[ValidationResult]:
        """Validate all documentation files."""
        results = []
        
        # Validate directory structure
        results.extend(self._validate_directory_structure())
        
        # Validate individual files
        for file_path in self.root_dir.rglob("*.md"):
            if "templates" not in str(file_path) and "validation" not in str(file_path):
                results.extend(self._validate_file(file_path))
        
        return results

    def _validate_directory_structure(self) -> List[ValidationResult]:
        """Validate the documentation directory structure."""
        results = []
        required_dirs = [
            "1. Project Overview",
            "2. Product Documentation",
            "3. Technical Documentation",
            "4. Development",
            "5. Operations"
        ]
        
        for dir_name in required_dirs:
            dir_path = self.root_dir / dir_name
            if not dir_path.exists():
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    message=f"Missing required directory: {dir_name}",
                    file=str(dir_path)
                ))
        
        return results

    def _validate_file(self, file_path: Path) -> List[ValidationResult]:
        """Validate a single documentation file."""
        results = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check metadata
        results.extend(self._validate_metadata(content, file_path))
        
        # Check required sections
        results.extend(self._validate_sections(content, file_path))
        
        # Check markdown standards
        results.extend(self._validate_markdown_standards(content, file_path))
        
        # Check links
        results.extend(self._validate_links(content, file_path))
        
        return results

    def _validate_metadata(self, content: str, file_path: Path) -> List[ValidationResult]:
        """Validate document metadata."""
        results = []
        
        for field in self.validation_rules["required_metadata"]:
            pattern = rf"\*{field}:\s*.*\*"
            if not re.search(pattern, content):
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    message=f"Missing required metadata: {field}",
                    file=str(file_path)
                ))
        
        return results

    def _validate_sections(self, content: str, file_path: Path) -> List[ValidationResult]:
        """Validate required sections."""
        results = []
        
        for section in self.validation_rules["required_sections"]:
            pattern = rf"^#+\s+{section}$"
            if not re.search(pattern, content, re.MULTILINE):
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    message=f"Missing required section: {section}",
                    file=str(file_path)
                ))
        
        return results

    def _validate_markdown_standards(self, content: str, file_path: Path) -> List[ValidationResult]:
        """Validate markdown formatting standards."""
        results = []
        
        # Check line length
        for i, line in enumerate(content.split('\n'), 1):
            if len(line) > self.validation_rules["markdown_standards"]["max_line_length"]:
                results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    message=f"Line exceeds maximum length ({self.validation_rules['markdown_standards']['max_line_length']} characters)",
                    file=str(file_path),
                    line=i
                ))
        
        # Check heading levels
        for i, line in enumerate(content.split('\n'), 1):
            if line.startswith('#'):
                level = len(line.split()[0])
                if level > len(self.validation_rules["markdown_standards"]["heading_levels"]):
                    results.append(ValidationResult(
                        level=ValidationLevel.WARNING,
                        message="Heading level too deep",
                        file=str(file_path),
                        line=i
                    ))
        
        # Check code blocks
        code_blocks = re.findall(r'```(\w+)?\n.*?```', content, re.DOTALL)
        for block in code_blocks:
            if block and block not in self.validation_rules["markdown_standards"]["code_block_languages"]:
                results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    message=f"Unsupported code block language: {block}",
                    file=str(file_path)
                ))
        
        return results

    def _validate_links(self, content: str, file_path: Path) -> List[ValidationResult]:
        """Validate markdown links."""
        results = []
        
        # Find all markdown links
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        
        for link_text, link_url in links:
            # Check for broken links
            if link_url.startswith('http'):
                # External links - could add HTTP validation here
                pass
            else:
                # Internal links
                target_path = (file_path.parent / link_url).resolve()
                if not target_path.exists():
                    results.append(ValidationResult(
                        level=ValidationLevel.ERROR,
                        message=f"Broken link: {link_url}",
                        file=str(file_path)
                    ))
        
        return results

def main():
    """Main function to run documentation validation."""
    validator = DocumentationValidator("docs")
    results = validator.validate_documentation()
    
    # Print results
    error_count = 0
    warning_count = 0
    
    for result in results:
        if result.level == ValidationLevel.ERROR:
            error_count += 1
            logger.error(f"{result.file}:{result.line if result.line else ''} - {result.message}")
        elif result.level == ValidationLevel.WARNING:
            warning_count += 1
            logger.warning(f"{result.file}:{result.line if result.line else ''} - {result.message}")
        else:
            logger.info(f"{result.file}:{result.line if result.line else ''} - {result.message}")
    
    # Summary
    logger.info(f"\nValidation Summary:")
    logger.info(f"Total files checked: {len(list(Path('docs').rglob('*.md')))}")
    logger.info(f"Errors: {error_count}")
    logger.info(f"Warnings: {warning_count}")
    
    # Exit with error if there are validation errors
    if error_count > 0:
        exit(1)

if __name__ == "__main__":
    main() 