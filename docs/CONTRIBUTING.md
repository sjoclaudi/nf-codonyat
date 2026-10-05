# Contributing to nf-codonyat

Thank you for considering contributing to nf-codonyat! This document provides guidelines for contributing to the project.

## Code of Conduct

Please note that this project is released with a [Code of Conduct](../CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue on GitHub with:
- A clear, descriptive title
- Steps to reproduce the issue
- Expected vs. actual behavior
- Your environment (OS, Nextflow version, container/conda)
- Relevant log files or error messages

### Suggesting Enhancements

Enhancement suggestions are welcome! Please create an issue describing:
- The enhancement and its motivation
- How it would be used
- Any potential implementation approaches

### Pull Requests

1. Fork the repository
2. Create a new branch for your feature or fix
3. Make your changes, following the style guidelines
4. Add or update tests as needed
5. Update documentation as needed
6. Run the test suite to ensure everything works
7. Submit a pull request

#### Pull Request Guidelines

- Follow the Nextflow best practices
- Include clear commit messages
- Update CHANGELOG.md with a description of your changes
- Ensure tests pass (`nf-test test` and the test profile)
- Keep the research-use-only scope in mind

## Development Setup

```bash
# Clone the repository
git clone https://github.com/sjoclaudi/nf-codonyat.git
cd nf-codonyat

# Run linting
nextflow lint .

# Build the Docker image (for local testing)
docker build -t ghcr.io/sjoclaudi/nf-codonyat:dev .

# Run tests
nf-test test --profile docker
nextflow run . -profile test,docker
```

## Style Guide

- Use 4 spaces for indentation in Nextflow files
- Follow the nf-core style guide where applicable
- Keep line length to ~120 characters
- Add comments for complex logic
- Use meaningful variable and process names

## Testing

All changes should include appropriate tests:
- Add nf-test cases for new processes or changes to existing ones
- Ensure the test profile runs successfully
- Verify outputs match expected results

## Documentation

Update documentation when:
- Adding new parameters or features
- Changing input/output formats
- Modifying the pipeline workflow
- Adding dependencies or requirements

Key documentation files:
- `README.md` - Main documentation
- `docs/usage.md` - Usage instructions
- `docs/output.md` - Output descriptions
- `nextflow_schema.json` - Parameter schema
- `CHANGELOG.md` - Version history

## Questions?

If you have questions about contributing, feel free to:
- Open an issue for discussion
- Review existing issues and pull requests
- Check the nf-core contributing guidelines for general Nextflow best practices

Thank you for your contributions!
