# Version Control & Document Management Strategy

*Version: 1.0.0*  
*Created: April 5, 2025*  
*Owner: Project Manager*

## Overview

This document outlines the version control and document management strategy for the Guards & Robbers project. It establishes clear guidelines for maintaining consistent versioning across all project artifacts, ensuring traceability between documentation and code changes, and implementing a robust document review process.

## Table of Contents

- [Version Numbering Scheme](#version-numbering-scheme)
- [Document Version Control](#document-version-control)
- [Code Version Control](#code-version-control)
- [Release Management](#release-management)
- [Document Review Process](#document-review-process)
- [Automation Tools](#automation-tools)
- [Version History Registry](#version-history-registry)

## Version Numbering Scheme

The project follows Semantic Versioning 2.0.0 (SemVer) for all artifacts:

**Format: MAJOR.MINOR.PATCH**

- **MAJOR**: Incremented for incompatible API changes or significant feature redesigns
- **MINOR**: Incremented for backward-compatible functionality additions
- **PATCH**: Incremented for backward-compatible bug fixes

Additional qualifiers may be appended for pre-releases (e.g., `1.2.0-alpha.1`).

### Version Synchronization

All primary project documentation must share the same MAJOR.MINOR version as the codebase:

1. Code repository tags determine the canonical version
2. Core documentation (README.md, dev_plan.md) must match this version
3. Supporting documentation may have independent PATCH versions

### Example Version Matrix

| Artifact | Current Version | Notes |
|----------|----------------|-------|
| Codebase | 1.2.0 | Released April 5, 2025 |
| README.md | 1.2.0 | Must match codebase MAJOR.MINOR |
| dev_plan.md | 1.2.0 | Must match codebase MAJOR.MINOR |
| ml_enhancement_plan.md | 1.0.0 | Independent versioning |
| API documentation | 1.2.0 | Must match codebase MAJOR.MINOR.PATCH |

## Document Version Control

### Documentation Metadata

All documentation must include:

1. **Version number**: Following SemVer scheme
2. **Last updated date**: In YYYY-MM-DD format
3. **Document owner**: Role responsible for maintenance
4. **Contributors**: List of primary contributors (optional)

### Change History Requirements

All documentation must include a change log with:

1. Version number
2. Date of change
3. Author of change
4. Brief description of changes

### Document Storage

1. **Location**: All documentation is stored in the main Git repository
2. **Format**: Markdown (.md) for all text documentation
3. **Graphics**: Images stored in `/docs/images/` directory, referenced relatively

## Code Version Control

### Git Repository Structure

The repository follows the GitFlow branching model:

1. `main`: Production-ready code, tagged with version numbers
2. `develop`: Integration branch for features
3. `feature/*`: Feature development branches
4. `bugfix/*`: Bug fix branches
5. `release/*`: Release preparation branches
6. `hotfix/*`: Production emergency fixes

### Commit Message Format

All commits must follow the Conventional Commits format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types include: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Branch Protection Rules

1. `main` and `develop` branches require pull request approvals
2. Status checks must pass before merging
3. Linear history maintained through rebase or squash merging

## Release Management

### Release Process

1. Create a `release/vX.Y.Z` branch from `develop`
2. Update version numbers in all documentation
3. Generate/update change logs
4. Create a pull request to `main`
5. After approval and merge, tag the release in Git
6. Deploy to production environment
7. Merge changes back to `develop`

### Release Artifacts

Each release must include:

1. Tagged Git commit
2. Updated documentation with matching version numbers
3. Release notes summarizing changes
4. Deployment package for production

## Document Review Process

### Review Requirements

All documentation changes must be:

1. Subjected to peer review before merging
2. Validated for version number consistency
3. Checked for formatting and style compliance
4. Verified for technical accuracy

### Review Checklist

- [ ] Version numbers are consistent with codebase
- [ ] Last updated date is current
- [ ] Change log is updated with appropriate details
- [ ] Links to other documents/sections are valid
- [ ] No confidential information is exposed
- [ ] Formatting follows project standards
- [ ] Technical information is accurate

## Automation Tools

### Version Management

1. **Version Bumping Script**: Automates version updates across files
   - Usage: `bump_version.py --type minor`
   - Updates all relevant files with new version numbers

2. **Version Consistency Checker**: CI/CD check for version mismatches
   - Validates documentation versions match code when appropriate
   - Runs on all pull requests to `develop` and `main`

### Documentation Generation

1. **API Documentation**: Auto-generated from code comments
   - Updated during the release process
   - Version number derived from codebase

2. **Change Log Generator**: Creates change logs from commit messages
   - Utilizes conventional commit format
   - Categorizes changes by type

## Version History Registry

The project maintains a centralized version history registry:

```json
{
  "latest": "1.2.0",
  "releases": [
    {
      "version": "1.2.0",
      "date": "2025-04-05",
      "commit": "ed78e14a1b...",
      "highlights": [
        "Added newsletter subscription system",
        "Implemented ML enhancement plan",
        "Updated project phases"
      ],
      "documents": [
        {"name": "README.md", "version": "1.2.0"},
        {"name": "dev_plan.md", "version": "1.2.0"},
        {"name": "ml_enhancement_plan.md", "version": "1.0.0"}
      ]
    },
    {
      "version": "1.1.0",
      "date": "2025-04-04",
      "commit": "cf02d6a9a9...",
      "highlights": [
        "Added admin dashboard",
        "Implemented MongoDB fallback",
        "Added test suite"
      ]
    },
    {
      "version": "1.0.0",
      "date": "2025-04-03",
      "commit": "8c61c1bee2...",
      "highlights": [
        "Initial production release",
        "MongoDB integration",
        "Flask backend"
      ]
    }
  ]
}
```

This registry serves as a single source of truth for project versioning.

## Implementation Plan

1. Create version bumping script (Priority: High)
2. Add version validation to CI/CD pipeline (Priority: Medium)
3. Establish centralized version history registry (Priority: Medium)
4. Train team on version management procedures (Priority: High)

---

By adhering to this strategy, the Guards & Robbers project will maintain clear traceability between code and documentation, ensure version consistency, and streamline the release management process. 