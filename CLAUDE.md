# CLAUDE.md
You are an expert in the Python programming language and developing tools using the newest combination of Python tools. That means as of right now, the current versions and tools I expect to see used are:

- Python 3.11
- poetry
- argparse
- pydantic 2 (for data validation)
- pytest (for testing)
- ty and mypy (for type checking)

Typing and data validation are very important to my work. So, please make use of them where possible. This means that you will define types rather than returning complicated data structures of dicts and lists. Use `dict` and `list` for types as you can for newer versions of Python. Optional variables should use the new union syntax, such as: `foo: str|None = None`.

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ras-search_ai-rag-westlaw-50-states-survey** is a Celery-based worker service that processes jurisdictional survey requests using RAG (Retrieval-Augmented Generation) for legal research. It is part of the Research Application Services (RAS) AI Acceleration platform.

The service integrates with the `labs-aalp-jurisdictional-survey-service` library to generate answers about legal jurisdictions across US states using AI-powered document retrieval and summarization.

## Architecture

### Core Components

1. **Celery Worker Application** (`app/main.py`)
   - Entry point that creates and configures the Celery worker
   - Runs as a solo worker with concurrency=1 to manage memory
   - Configured with pickle serialization for complex task payloads

2. **Worker Tasks** (`app/worker/v4/action_sequencing_tasks.py`)
   - Implements `start_next_action_task` as the main Celery task
   - Extends `ActionSequenceTaskBaseV4` from `conversation-core` library
   - Handles blue/green deployment queue routing

3. **Services Architecture** (all in `app/services/v4/`)
   - `ConversationService`: Orchestrates RAG workflow, integrates with LegislationSurveyService
   - `ActionSequenceService`: Routes between VALIDATION and RAG action types
   - `ValidationService`: Validates user inputs and jurisdiction parameters

4. **Blue/Green Deployment** (`app/config/celery_config.py`)
   - Uses Helm service to detect blue vs green deployment state
   - Automatically switches queue consumption when deployment state changes
   - Poller runs every 10s in green state to detect blue activation

### Key Dependencies

- **conversation-core**: Shared library providing base classes for task handling, DynamoDB interactions, and answer profiling
- **labs-aalp-jurisdictional-survey-service**: Core RAG service for jurisdiction-specific legal queries
- **gcs-utils**: Entitlement and authentication against GCS (presumed internal service)
- **configuration-utils**: Shared configuration management across RAS services

### Data Flow

1. Task arrives on queue (`westlaw_50ss` + blue/green suffix)
2. `start_next_action_task` receives action sequence from conversation system
3. Action type routes to either:
   - VALIDATION: Validates jurisdictions and input format
   - RAG: Calls `LegislationSurveyService` to generate legal survey answers
4. Results stored in DynamoDB and S3 (via ConversationDBV2)
5. Metrics sent to DataDog for monitoring

## Development Setup

### Environment Configuration

Required environment variables (set in `.env.local` for local development):
```bash
PYTHONUNBUFFERED=1
DD_ENV=local
DD_PROFILING_ENABLED=false
DD_SERVICE=ai-rag-westlaw-50-states-survey
DD_TRACE_ENABLED=True
DD_VERSION=0.0.1
RESOURCES_DIR=./app/config/resources
HOSTNAME=[your workstation name]
```

Working directory must be set to repository root.

### Dependencies

Install dependencies using Poetry:
```bash
poetry install
```

To update dependencies (especially the testing module):
```bash
poetry update
```

The project uses Python 3.11 and dependencies from Thomson Reuters internal Artifactory at `https://tr1.jfrog.io/artifactory/api/pypi/pypi/simple`.

### Running Locally

To run the Celery worker locally:
```bash
python -m app.main
```

This starts a solo Celery worker that listens on the `westlaw_50ss` queue.

**Note**: This is a backend worker that depends on `ai-conversations` and `ai-rag-westlaw` services running locally for full functionality.

## Testing

### Run All Tests

Using pytest directly:
```bash
pytest
```

Using Poetry task runner:
```bash
poetry run poe pytest
```

This runs tests with coverage reports generated in `reports/` directory:
- `reports/pytest_junit.xml`: JUnit format results
- `reports/pytest.html`: HTML test report
- `reports/coverage_html/`: HTML coverage report
- `reports/coverage.xml`: XML coverage report

### Run a Single Test

```bash
pytest tests/services/v4/test_conversation_service.py::test_name -v
```

Or for a specific test file:
```bash
pytest tests/services/v4/test_conversation_service.py -v
```

### Smoke Tests

Smoke tests require cloud-tool access to `ras-search-preprod` AWS account for GCS authentication.

**Prerequisites**:
- Cloud-tool into `ras-search-preprod` account
- Have `ai-conversations` and `ai-rag-westlaw` running locally

```bash
poetry update
cd .venv/Lib/site-packages/
pytest -v -s -m rag_westlaw ./ai_conversations_qa_testing/ --dns http://localhost:8010
```

Note: Commands shown are for PowerShell; syntax may differ for other shells.

### Test Organization

- `tests/services/v4/`: Tests for v4 service implementations
- `tests/worker/`: Tests for Celery task implementations
- `tests/utils/`: Tests for utility functions
- `tests/conftest.py`: Shared fixtures and mocks

Tests use extensive mocking of AWS services (DynamoDB, S3, SES), GCS, and conversation-core components.

## Code Quality

### Linting and Formatting

The project uses Black for code formatting:
```bash
black app/ tests/
```

Configuration in `pyproject.toml`:
- Line length: 120 characters
- Target version: Python 3.9+

## Docker

Build the Docker image (requires Artifactory credentials):
```bash
docker build \
  --build-arg REGION_LONG=us-east-1 \
  --build-arg ARTIFACTORY_USER=your-user \
  --build-arg ARTIFACTORY_TOKEN=your-token \
  -t ras-search-ai-rag-westlaw-50-states-survey .
```

The Dockerfile uses a multi-stage build with TR Chainguard Python 3.11 FIPS-compliant base image.

## Important Notes

### Task Configuration

- **Task timeout**: 59 minutes (soft) / 60 minutes (hard)
- **Worker lifecycle**: Max 10 tasks per worker child before restart
- **Memory limit**: 2.5GB per child worker
- **Message acknowledgment**: Late acknowledgment (`task_acks_late=True`) ensures message persistence if pod is killed
- **Prefetch**: Disabled (`worker_prefetch_multiplier=1`) to prevent task loss

### Settings and Configuration

All settings are loaded via `app/config/settings.py` which extends `CoreSettings` from `configuration-utils`. Settings are region-aware and support automatic region value replacement.

The `RESOURCES_DIR` environment variable must point to `./app/config/resources` for proper resource file loading.

### Conversation Core Integration

This service follows the conversation-core v4 patterns:
- Extends `ActionSequenceTaskBaseV4` for task handling
- Uses `ConversationDBV2` for state persistence
- Implements `ConversationServiceBaseV4` for RAG operations
- Follows action sequencing model where tasks can chain multiple actions

### Testing with Mocks

Tests heavily mock external dependencies. Key mocked components in `conftest.py`:
- DynamoDB (ConversationDB v1 and v2)
- S3 / SES via boto3
- EntitlementClient
- AnswerProfileService

When writing new tests, use the fixtures defined in `conftest.py` to maintain consistency.

## Common Issues

1. **Import errors**: Ensure `PYTHONPATH` includes the `app` directory. Pytest is configured with `pythonpath = app` in `pytest.ini`.

2. **Resource file not found**: Verify `RESOURCES_DIR` environment variable is set to `./app/config/resources`.

3. **Async event loop issues**: The service uses `get_or_create_eventloop()` utility to manage asyncio loops in Celery worker context.

4. **Queue not found**: Ensure blue/green deployment state is correctly detected via Helm service.
