# Test Suite for ToolM8 CSV Import System

This directory contains comprehensive unit tests for the parser-centric CSV import system.

## Test Coverage

### 🎯 Core Components

1. **`test_base_csv_parser.py`** - Base CSV Parser Interface
   - Abstract class enforcement
   - Standard tool format validation
   - Abstract method implementation requirements

2. **`test_taaft_csv_parser.py`** - TAAFT CSV Parser
   - CSV format validation
   - Data parsing and transformation
   - String cleaning and slug generation
   - URL cleaning and pricing extraction
   - Quality and popularity scoring
   - Row transformation logic

3. **`test_base_csv_importer.py`** - Base CSV Importer
   - CSV import workflow
   - Bulk operations (upsert vs insert)
   - Duplicate handling logic
   - Error handling and logging
   - Database interaction mocking

4. **`test_csv_importer_factory.py`** - Factory Pattern
   - Source registration and retrieval
   - Case-insensitive source matching
   - Error handling for unsupported sources
   - Dynamic importer creation

5. **`test_csv_import_endpoint.py`** - FastAPI Endpoint
   - HTTP request/response handling
   - File upload validation
   - Source parameter validation
   - Error response formats
   - Logging verification

### 🧪 Test Types

- **Unit Tests**: Individual component testing with mocks
- **Integration Tests**: Component interaction testing
- **Error Handling**: Exception scenarios and edge cases
- **Validation Tests**: Input validation and format checking
- **Mock Testing**: Database and external dependency mocking

## Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_taaft_csv_parser.py -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html

# Run tests by pattern
python -m pytest tests/ -k "parser" -v
```

## Test Philosophy

### Parser-Centric Testing
Tests emphasize that **parsers are the critical component** since each CSV source has different formats:

- **Parser Tests**: Comprehensive coverage of format-specific logic
- **Importer Tests**: Focus on generic bulk operations
- **Factory Tests**: Registration and source management
- **Endpoint Tests**: HTTP layer and validation

### Mock Strategy
- **Database Operations**: Mocked to avoid external dependencies
- **File Operations**: Use BytesIO for in-memory file testing
- **Factory Pattern**: Mock importers for isolated testing
- **Async Operations**: Proper AsyncMock usage

## Key Test Scenarios

### ✅ Parser Testing
- CSV format validation
- Data transformation accuracy
- Edge cases (empty data, invalid formats)
- String cleaning and normalization
- Pricing type extraction
- Quality score calculations

### ✅ Importer Testing
- Bulk upsert operations
- Duplicate detection and handling
- Error scenarios and recovery
- Replace vs skip existing logic
- Database interaction patterns

### ✅ Factory Testing
- Source registration
- Case-insensitive matching
- Error handling
- Dynamic importer creation

### ✅ Endpoint Testing
- File upload validation
- Parameter validation
- Error response formats
- Success scenarios
- HTTP status codes

## Test Data

Tests use realistic sample data:
- Valid CSV formats for TAAFT
- Invalid CSV scenarios
- Edge cases (empty files, large files)
- Various pricing formats
- Different tool types

## Mock Objects

- **MockParser**: Simulates CSV parsing behavior
- **MockImporter**: Tests importer interface
- **MockClient**: Database client simulation
- **BytesIO**: In-memory file objects

## Assertions

Tests verify:
- **Functional Correctness**: Expected outputs for given inputs
- **Error Handling**: Proper exception raising and handling
- **Data Validation**: Format and type checking
- **State Management**: Object state changes
- **Integration**: Component interaction

The test suite provides confidence in the parser-centric architecture and ensures reliable CSV import functionality across different data sources.