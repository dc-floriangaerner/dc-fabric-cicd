---
applyTo: "scripts/**/*.py"
description: "Python scripts for Fabric CI/CD deployment and management"
---

# Python Scripts Instructions

## Specific Guidelines for scripts/ Directory

### Module Structure

Scripts in the `scripts/` directory are organized as a Python package:

- Use **relative imports** for local modules: `from .module import function`
- Files use **underscore naming**: `deploy_to_fabric.py` (not hyphens)
- Execute as modules: `python -m scripts.deploy_to_fabric`

### Coding Standards

- **Python Version**: 3.11+
- **Type Hints**: Always use type hints for function parameters and return types
- **Error Handling**: Catch specific exceptions, use `sys.exit(1)` for errors
- **Logging**: Use centralized logger from `scripts.common.logger`: `logger = get_logger(__name__)`
- **Docstrings**: Include for all public functions with Args and Returns sections

### Code Quality

All Python code should pass tests and keep type hints accurate.

**Run before committing:**
```bash
# Run tests
pytest tests/ -v

# Type-check scripts
mypy scripts/
```

### Error Handling Pattern

```python
from azure.core.exceptions import HttpResponseError
from ..common.logger import get_logger

logger = get_logger(__name__)

try:
    # API operation
    result = client.do_something()
except HttpResponseError as e:
    # Use str(e) to get error message, NOT e.message
    logger.error(f"Operation failed: {str(e)}")
    sys.exit(1)
```

### Authentication

Use `azure-identity` for authentication. The deployment credentials are read from environment variables by `create_azure_credential()` in `deploy_to_fabric.py`:

```python
from azure.identity import ClientSecretCredential

credential = ClientSecretCredential(
    tenant_id=tenant_id,
    client_id=client_id,
    client_secret=client_secret
)
```

### Common Patterns

**Configuration Management:**
- Constants defined in `scripts/fabric/config.py`
- Import as: `from .fabric.config import VALID_ENVIRONMENTS`

**Return Values:**
- Return `bool` for success/failure operations
- Return `None` or raise exceptions for errors
- Always provide clear error messages

### Testing

This is a reference architecture - no automated tests required for scripts. Manual validation:
- Test locally before committing
- Verify deployment with actual Fabric workspaces
- Check GitHub Actions logs for errors

### Files in This Directory

- `deploy_to_fabric.py` - Main deployment orchestration script
- `fabric/config.py` - Centralized configuration constants
- `fabric_workspace_manager.py` - Workspace management utilities
- `generate_deployment_summary.sh` - Bash script for deployment summaries
- `*.ipynb` - Jupyter notebooks for API exploration (not used in CI/CD)
