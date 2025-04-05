#!/usr/bin/env python3
"""
Spell Checker Integration
Version: 1.0.0
Last Updated: May 16, 2025
"""

import re
from pathlib import Path
from typing import List, Dict
import logging
from dataclasses import dataclass
from enum import Enum
import pyspellchecker
import yaml

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
class SpellCheckResult:
    level: ValidationLevel
    message: str
    file: str
    line: int
    word: str
    suggestions: List[str]

class DocumentationSpellChecker:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.spell = pyspellchecker.SpellChecker()
        self.custom_words = self._load_custom_words()
        self.ignore_patterns = self._load_ignore_patterns()
        
    def _load_custom_words(self) -> List[str]:
        """Load custom words from YAML file."""
        words_file = self.root_dir / "validation" / "custom_words.yaml"
        if words_file.exists():
            with open(words_file, 'r') as f:
                return yaml.safe_load(f).get('words', [])
        return []
        
    def _load_ignore_patterns(self) -> List[str]:
        """Load patterns to ignore from YAML file."""
        patterns_file = self.root_dir / "validation" / "ignore_patterns.yaml"
        if patterns_file.exists():
            with open(patterns_file, 'r') as f:
                return yaml.safe_load(f).get('patterns', [])
        return [
            r'```.*?```',  # Code blocks
            r'`.*?`',      # Inline code
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',  # URLs
            r'[A-Z][a-z]+[A-Z][a-zA-Z]+',  # CamelCase
            r'\d+',        # Numbers
        ]
        
    def check_file(self, file_path: Path) -> List[SpellCheckResult]:
        """Check spelling in a single file."""
        results = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Remove content to ignore
        for pattern in self.ignore_patterns:
            content = re.sub(pattern, '', content, flags=re.DOTALL)
            
        # Split into words
        words = re.findall(r'\b\w+\b', content)
        
        # Check each word
        for i, word in enumerate(words):
            if (word.lower() not in self.custom_words and 
                not self.spell.known([word]) and 
                len(word) > 1):  # Ignore single characters
                suggestions = self.spell.candidates(word)
                results.append(SpellCheckResult(
                    level=ValidationLevel.WARNING,
                    message=f"Possible misspelling: {word}",
                    file=str(file_path),
                    line=i + 1,
                    word=word,
                    suggestions=list(suggestions)[:5] if suggestions else []
                ))
                
        return results
        
    def check_all_files(self) -> Dict[str, List[SpellCheckResult]]:
        """Check spelling in all documentation files."""
        results = {}
        
        for file_path in self.root_dir.rglob("*.md"):
            if "templates" not in str(file_path) and "validation" not in str(file_path):
                file_results = self.check_file(file_path)
                if file_results:
                    results[str(file_path)] = file_results
                    
        return results

def main():
    """Main function to run spell checking."""
    checker = DocumentationSpellChecker("docs")
    results = checker.check_all_files()
    
    # Print results
    total_issues = 0
    
    for file_path, file_results in results.items():
        logger.info(f"\nChecking {file_path}:")
        for result in file_results:
            total_issues += 1
            logger.warning(f"Line {result.line}: {result.message}")
            if result.suggestions:
                logger.info(f"  Suggestions: {', '.join(result.suggestions)}")
                
    # Summary
    logger.info(f"\nSpell Check Summary:")
    logger.info(f"Total files checked: {len(list(Path('docs').rglob('*.md')))}")
    logger.info(f"Total issues found: {total_issues}")
    
    # Exit with warning if there are spelling issues
    if total_issues > 0:
        exit(1)

if __name__ == "__main__":
    main() 