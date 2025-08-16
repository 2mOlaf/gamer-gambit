# Testing Framework for Jarvfjallet Discord Bot

This directory contains a comprehensive testing framework for the Jarvfjallet Discord bot, designed to test bot functionality without requiring actual Discord API connections.

## Overview

The testing framework includes:

- **Unit Tests**: Fast, isolated tests that mock external dependencies
- **Integration Tests**: Tests that use real database connections but mock Discord
- **Mock Objects**: Comprehensive Discord.py object mocks for testing
- **Database Testing**: Utilities for testing with temporary databases
- **Command Testing**: Full Discord command workflow testing

## Structure

```
tests/
├── conftest.py                           # Shared fixtures and configuration
├── mocks/
│   └── discord_mocks.py                  # Mock Discord objects
├── unit/
│   ├── test_database.py                  # Database functionality tests
│   └── test_game_assignment_cog.py       # Game assignment command tests
├── integration/
│   └── test_game_assignment_integration.py # Full workflow integration tests
└── README.md                            # This file
```

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run Specific Test Categories
```bash
# Unit tests only (fast)
pytest -m unit

# Integration tests only (slower)
pytest -m integration

# Database tests only
pytest -m database
```

### Run Specific Test Files
```bash
# Database tests
pytest tests/unit/test_database.py

# Game assignment tests
pytest tests/unit/test_game_assignment_cog.py

# Integration tests
pytest tests/integration/test_game_assignment_integration.py
```

### Run Specific Tests
```bash
# Single test function
pytest tests/unit/test_database.py::TestDatabaseOperations::test_database_initialization

# Test with verbose output
pytest tests/unit/test_game_assignment_cog.py -v
```

## Mock Objects

### MockBot
Simulates a Discord bot instance with database connections.

### MockDiscordInteraction
Simulates Discord slash command interactions with:
- Response deferral tracking
- Followup message tracking
- User information
- Channel information (if needed)

### MockDiscordUser
Simulates Discord users with:
- User ID
- Display name
- DM sending capabilities

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
- Fast tests that run in isolation
- Mock all external dependencies
- Test individual functions and classes
- Should run in under 1 second per test

### Integration Tests (`@pytest.mark.integration`)
- Test complete workflows
- Use real database connections (but temporary)
- Mock only Discord API calls
- Test interaction between components

### Database Tests (`@pytest.mark.database`)
- Test database operations
- Use temporary SQLite databases
- Verify CRUD operations
- Test data integrity

## Writing New Tests

### Unit Test Example
```python
import pytest
from unittest.mock import AsyncMock
from cogs.my_cog import MyCog

@pytest.mark.unit
class TestMyCog:
    def test_cog_initialization(self, mock_bot):
        """Test cog initializes correctly"""
        cog = MyCog(mock_bot)
        assert cog.bot == mock_bot

    async def test_my_command(self, my_cog, mock_interaction):
        """Test async command functionality"""
        # Setup mocks
        my_cog.bot.database.some_method = AsyncMock(return_value=test_data)
        
        # Execute command
        await my_cog.my_command(mock_interaction)
        
        # Verify results
        assert mock_interaction.response.deferred is True
        my_cog.bot.database.some_method.assert_called_once()
```

### Integration Test Example
```python
import pytest
from cogs.my_cog import MyCog
from utils.database import Database

@pytest.mark.integration
class TestMyIntegration:
    @pytest.fixture
    async def real_database(self):
        """Create real database for integration testing"""
        # Setup temporary database
        # ... implementation
        yield db

    async def test_full_workflow(self, real_database, mock_interaction):
        """Test complete command workflow"""
        bot = MockBot()
        bot.database = real_database
        cog = MyCog(bot)
        
        # Test complete workflow
        await cog.my_command(mock_interaction)
        
        # Verify database state changed
        result = await real_database.get_some_data()
        assert result is not None
```

## Fixtures

### Available Fixtures
- `temp_db_path`: Temporary database file path
- `test_database`: Pre-populated test database
- `mock_bot`: Mock Discord bot instance
- `mock_interaction`: Mock Discord interaction
- `game_assignment_cog`: GameAssignment cog instance
- `sample_game_data`: Sample game data for testing

### Creating Custom Fixtures
```python
@pytest.fixture
async def my_custom_fixture():
    """Create custom test data"""
    data = create_test_data()
    yield data
    # Cleanup if needed
```

## Best Practices

### Do's
- ✅ Use appropriate test markers (`@pytest.mark.unit`, etc.)
- ✅ Mock external dependencies in unit tests
- ✅ Test both success and failure scenarios
- ✅ Use descriptive test names
- ✅ Keep tests focused and independent
- ✅ Clean up resources in fixtures

### Don'ts
- ❌ Don't make actual Discord API calls in tests
- ❌ Don't use production databases
- ❌ Don't write tests that depend on external services
- ❌ Don't write overly complex tests
- ❌ Don't ignore test failures

## Configuration

Test configuration is handled in:
- `pytest.ini`: Main pytest configuration
- `conftest.py`: Fixtures and test setup
- `requirements-test.txt`: Test dependencies

## Troubleshooting

### Common Issues

**Async function errors**: Make sure functions are properly marked as async and use appropriate fixtures.

**Import errors**: Check that your module paths are correct and modules are properly installed.

**Database errors**: Ensure database fixtures are properly set up and cleaned up.

**Mock assertion failures**: Verify that mocks are configured correctly and methods are being called as expected.

### Running Tests with Debug Output
```bash
# Verbose output
pytest tests/ -v

# Show print statements
pytest tests/ -s

# Stop on first failure
pytest tests/ -x

# Show local variables in tracebacks
pytest tests/ -l
```

## Adding New Test Categories

To add new test categories:

1. Add marker to `pytest.ini`:
```ini
markers =
    mytype: marks tests as mytype tests
```

2. Use marker in tests:
```python
@pytest.mark.mytype
def test_my_function():
    pass
```

3. Run category:
```bash
pytest -m mytype
```

## Future Improvements

- Add performance benchmarking tests
- Add test coverage reporting
- Add automated test data generation
- Add visual test result reporting
- Add continuous integration support
