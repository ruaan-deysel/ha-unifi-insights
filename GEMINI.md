# ha-unifi-insights (UniFi Insights)

## Project Overview

**UniFi Insights** is a custom integration for Home Assistant that allows users to monitor and control their UniFi infrastructure directly from Home Assistant. It leverages the UniFi Network and Protect APIs to provide detailed insights into device status, performance metrics (CPU, memory, uplink), and control capabilities (restart).

### Key Features

- **Monitoring**: Device status (online/offline), CPU/Memory usage, Uptime, TX/RX rates.
- **Control**: Restart devices via Home Assistant services.
- **Multi-site Support**: Manage multiple UniFi sites.
- **Integration**: Works with UniFi Network and Protect (optional).

### Technology Stack

- **Language**: Python 3.11+
- **Platform**: Home Assistant (Custom Component)
- **Dependencies**: `unifi-official-api` (wrapper for UniFi APIs)
- **Testing**: `pytest`, `pytest-homeassistant-custom-component`
- **Linting/Formatting**: `ruff`, `mypy`

## Building and Running

### Prerequisites

- Python 3.11 or higher
- Home Assistant instance (for production) or local dev environment

### Development Setup

The project includes scripts to streamline the development process.

1.  **Install Dependencies:**

    ```bash
    ./scripts/setup
    ```

    This script installs the required Python packages defined in `requirements.txt`.

2.  **Run Development Server:**
    ```bash
    ./scripts/develop
    ```
    This script:
    - Creates a local `config` directory if it doesn't exist.
    - Configures `PYTHONPATH` to include the `custom_components` directory.
    - Starts a local Home Assistant instance with the integration loaded.
    - Access the instance at `http://localhost:8123`.

### Testing and Quality Assurance

Configuration for testing and linting is found in `pyproject.toml`.

- **Run Tests:**

  ```bash
  pytest
  ```

  Runs the test suite located in the `tests/` directory.

- **Linting and Formatting:**

  ```bash
  ruff check .
  ruff format .
  ```

  Uses `ruff` to enforce coding standards.

- **Type Checking:**
  ```bash
  mypy .
  ```
  Uses `mypy` for static type checking.

## Architecture

### Key Components

- **Entry Point (`__init__.py`)**: Handles the setup of the integration (`async_setup_entry`). It initializes the API clients (`UniFiNetworkClient`, `UniFiProtectClient`), validates connections, and sets up the `UnifiInsightsDataUpdateCoordinator`.
- **Data Coordinator (`coordinator.py`)**: Centralizes data fetching from the UniFi APIs to avoid spamming the controller. It manages the update interval and distributes data to entities.
- **Platforms**:
  - `sensor.py`: Numerical data (CPU, Memory, Uptime, Network rates).
  - `binary_sensor.py`: Boolean states (Device Online/Offline).
  - `switch.py`: Control entities (Restart Device).
  - `services.py`: Custom services (`refresh_data`, `restart_device`).
- **External Library**: Relies on `unifi-official-api` for the actual communication with UniFi controllers.

### Configuration Flow

The integration uses a Config Flow (`config_flow.py`) to guide users through the setup process in the Home Assistant UI, requiring:

- **Host URL**: The address of the UniFi Controller.
- **API Key**: A generated API key from the UniFi Controller (Admins & Users -> Create API Key).
- **Verify SSL**: Option to verify SSL certificates.

## Project Structure

```
.
├── custom_components/      # Source code for the integration
│   └── unifi_insights/
│       ├── __init__.py     # Component setup and entry point
│       ├── config_flow.py  # UI Configuration logic
│       ├── coordinator.py  # Data update coordinator
│       ├── manifest.json   # Integration metadata
│       ├── sensor.py       # Sensor platform
│       └── ...             # Other platforms (switch, binary_sensor, etc.)
├── scripts/                # Development helper scripts
│   ├── setup               # Install dependencies
│   └── develop             # Run local Home Assistant instance
├── tests/                  # Test suite
│   ├── conftest.py         # Pytest fixtures
│   └── ...                 # Test files
├── pyproject.toml          # Build system, test, and lint configuration
└── requirements.txt        # Python dependencies
```
