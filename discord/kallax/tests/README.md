# Kallax Discord Bot Testing Framework

A comprehensive testing suite for the Kallax Discord gaming bot, providing thorough coverage of all components from database operations to Discord command interactions.

## Overview

This testing framework provides:
- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions and workflows  
- **API Tests**: Test external API integrations (BGG, Steam, Xbox)
- **Database Tests**: Test data persistence and integrity
- **Performance Tests**: Ensure operations meet performance requirements
- **Mock Framework**: Complete Discord and API mocking for isolated testing

## Test Structure

```
tests/
├── unit/                           # Unit tests for individual components
│   ├── test_database.py            # Database operations and schema
│   ├── test_game_search_cog.py     # GameSearch cog commands
│   ├── test_user_profiles_cog.py   # UserProfiles cog commands  
│   ├── test_api_clients.py         # BGG/Steam/Xbox API clients
│   └── test_bot.py                 # Main bot class and event handling
├── integration/                    # Integration tests (to be created)
├── mocks/                         # Mock objects and fixtures
│   ├── discord_mocks.py           # Discord.py object mocks
│   └── api_mocks.py               # External API response mocks
├── conftest.py                    # Pytest fixtures and configuration
├── pytest.ini                    # Pytest settings and markers
└── requirements-test.txt          # Testing dependencies
```

## Features

### Comprehensive Mocking
- **Discord Objects**: Users, guilds, channels, interactions, embeds
- **API Responses**: Sample data for BGG, Steam, Xbox APIs
- **Database**: Temporary SQLite databases for testing
- **Async Support**: Full asyncio test support

### Test Categories

#### Unit Tests
- ✅ Database operations (CRUD, caching, integrity)
- ✅ GameSearch cog (search commands, API integration)
- ✅ UserProfiles cog (profile management, validation)
- ✅ API clients (BGG, Steam, Xbox communication)
- ✅ Bot class (initialization, event handling, cog management)

#### Test Markers
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.database` - Database-specific tests
- `@pytest.mark.api` - API client tests
- `@pytest.mark.performance` - Performance tests
- `@pytest.mark.asyncio` - Async test support

### Key Testing Areas

#### Database Testing (`test_database.py`)
- Schema creation and validation
- User profile CRUD operations
- Game caching and retrieval
- Game play tracking
- Server settings management
- Error handling and recovery
- Performance optimization
- SQL injection protection

#### Cog Testing (`test_game_search_cog.py`, `test_user_profiles_cog.py`)
- Command execution and validation
- Discord interaction handling
- API integration through cogs
- Error message formatting
- Permission and rate limiting
- Embed generation and formatting

#### API Client Testing (`test_api_clients.py`)
- HTTP request/response handling
- Data parsing (XML for BGG, JSON for Steam/Xbox)
- Error handling (timeouts, rate limits, auth)
- Response caching
- Concurrent request handling

#### Bot Core Testing (`test_bot.py`)
- Initialization and configuration
- Cog loading and management
- Event handling (ready, guild join/leave, errors)
- Health checks and metrics
- Graceful shutdown and recovery

## Setup and Usage

### Installation

```bash
# Install testing dependencies
pip install -r requirements-test.txt

# Or install individual packages
pip install pytest pytest-asyncio aiohttp aioresponses pytest-mock pytest-cov
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit                    # Unit tests only
pytest -m database                # Database tests only
pytest -m api                     # API tests only
pytest -m performance             # Performance tests only

# Run tests with coverage
pytest --cov=. --cov-report=html

# Run tests in specific files
pytest tests/unit/test_database.py
pytest tests/unit/test_game_search_cog.py

# Run with verbose output
pytest -v

# Run tests matching pattern
pytest -k "test_search"           # All search-related tests
pytest -k "test_database or test_api"  # Database or API tests
```

### Configuration

The testing framework is configured via `pytest.ini`:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --asyncio-mode=auto
markers = 
    unit: Unit tests
    integration: Integration tests
    database: Database tests
    api: API tests
    performance: Performance tests
```

## Test Data and Fixtures

### Core Fixtures (`conftest.py`)

- `mock_bot` - Discord bot instance with mocked methods
- `mock_user`, `mock_member`, `mock_guild` - Discord objects
- `mock_interaction`, `mock_dm_interaction` - Command interactions
- `temp_database`, `test_database` - Database instances
- `game_search_cog`, `user_profiles_cog` - Cog instances with mocks
- Sample data fixtures for games and profiles

### Mock Data

The framework includes realistic sample data:

```python
sample_bgg_game_data = {
    'bgg_id': 174430,
    'name': 'Gloomhaven', 
    'year_published': 2017,
    'rating': 8.7,
    'rating_count': 70000,
    'description': 'A campaign-driven board game...'
}
```

## Writing New Tests

### Unit Test Example

```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_board_game_success(game_search_cog, mock_interaction, 
                                       sample_bgg_game_data, mock_bgg_client):
    """Test successful board game search"""
    mock_bgg_client.search_games.return_value = [sample_bgg_game_data]
    game_search_cog.bgg_client = mock_bgg_client
    
    await game_search_cog.search_board_game(mock_interaction, "Gloomhaven")
    
    mock_bgg_client.search_games.assert_called_once_with("Gloomhaven")
    mock_interaction.response.send_message.assert_called_once()
```

### Database Test Example

```python
@pytest.mark.unit
@pytest.mark.database
async def test_create_user_profile(empty_database):
    """Test creating a new user profile"""
    success = await empty_database.create_user_profile(
        discord_id=123456789,
        bgg_username="testuser"
    )
    
    assert success is True
    
    profile = await empty_database.get_user_profile(123456789)
    assert profile is not None
    assert profile['bgg_username'] == "testuser"
```

## Best Practices

### Test Organization
- Group related tests in classes
- Use descriptive test names that explain the scenario
- Include both success and failure cases
- Test edge cases and error conditions

### Mocking Guidelines
- Mock external dependencies (APIs, Discord)
- Use real databases for database tests (with temporary files)
- Reset mocks between tests using fixtures
- Verify mock calls to ensure correct behavior

### Async Testing
- Mark async tests with `@pytest.mark.asyncio`
- Use `AsyncMock` for async methods
- Properly await async operations
- Handle async context managers correctly

### Performance Testing
- Set reasonable performance thresholds
- Test concurrent operations
- Monitor memory usage
- Test with realistic data sizes

## Coverage Goals

The framework aims for comprehensive test coverage:

- **Database Layer**: 95%+ coverage of all CRUD operations
- **Cog Commands**: 90%+ coverage of command paths and error handling
- **API Clients**: 85%+ coverage including error scenarios
- **Bot Core**: 80%+ coverage of initialization and event handling

## Continuous Integration

This testing framework is designed to integrate with CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pytest --cov=. --cov-report=xml
    
- name: Upload coverage
  uses: codecov/codecov-action@v1
```

## Future Enhancements

Planned additions to the testing framework:

- **Integration Tests**: End-to-end command workflows
- **Load Testing**: Concurrent user simulation
- **Database Migration Tests**: Schema evolution testing
- **API Contract Tests**: Verify external API compatibility
- **Security Tests**: Input validation and injection prevention

## Contributing

When adding new features to Kallax:

1. Write tests first (TDD approach)
2. Ensure new tests pass
3. Verify existing tests still pass
4. Update test documentation
5. Maintain coverage standards

## Troubleshooting

### Common Issues

**Tests fail with "RuntimeError: Event loop is closed"**
- Ensure `@pytest.mark.asyncio` is used for async tests
- Check that async fixtures properly clean up

**Database tests fail with permission errors**
- Ensure temporary directories are writable
- Check that database connections are properly closed

**API tests fail with network errors**
- Verify mock clients are properly configured
- Check that real API calls aren't being made in tests

### Debug Mode

Run tests with additional debugging:

```bash
# Enable debug logging
pytest --log-level=DEBUG

# Stop on first failure
pytest -x

# Enter debugger on failure
pytest --pdb
```

This comprehensive testing framework ensures the Kallax Discord bot maintains high quality and reliability as it evolves.
