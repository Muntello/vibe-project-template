# Testing Guide — {{PROJECT_NAME}}

---

## Running Tests

```bash
# All tests
{{TEST_COMMAND}}

# Specific test file
{{TEST_COMMAND_SPECIFIC}}

# With coverage report
{{TEST_COMMAND_COVERAGE}}

# By marker/tag (if supported)
{{TEST_PREFIX}} <test-runner> --tag=unit
{{TEST_PREFIX}} <test-runner> --tag=integration
```

## Test Markers / Tags

| Marker | Description | Speed |
|--------|-------------|-------|
| `unit` | No external dependencies, fast | Fast |
| `integration` | May need services (DB, cache, etc.) | Medium |
| `slow` | Performance or heavy operations | Slow |
| `e2e` | End-to-end tests | Slow |

## Coverage

- **Minimum threshold**: {{COVERAGE_TARGET}}%
- Coverage is checked automatically in the CI/CD pipeline
- Failures block deployment

## Test Structure

```
tests/
├── conftest / setup          # Shared fixtures / test setup
├── unit/                     # Fast, isolated tests
├── integration/              # Tests requiring services
└── e2e/                      # End-to-end tests (optional)
```

## Writing Tests

### Conventions

1. File names: match your framework's convention (`test_*.py`, `*.test.ts`, `*_test.go`, etc.)
2. Test names: describe the behavior being tested
3. Use shared fixtures/helpers for common setup
4. Mark tests with appropriate tags
5. Mock external services — never call real APIs in tests
6. Each test should be independent and idempotent

### CI Integration

Tests run automatically in CI before deployment. All tests must pass before merge.

---

**Last Updated**: {{DATE}}
