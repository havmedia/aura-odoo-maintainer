class ServiceError(Exception):
    """Base exception class for all service-related errors"""
    pass


class ServiceConfigurationError(ServiceError):
    """Base exception class for service configuration errors"""
    pass


class ServiceValidationError(ServiceConfigurationError):
    """Base exception class for service validation errors"""
    pass


class InvalidKeyError(ServiceValidationError):
    """Raised when an invalid configuration key is used"""

    def __init__(self, invalid_keys: set[str]):
        self.invalid_keys = invalid_keys
        super().__init__(f"Invalid configuration keys: {', '.join(invalid_keys)}")


class InvalidValueTypeError(ServiceValidationError):
    """Raised when a configuration value has an invalid type"""

    def __init__(self, key: str, expected_type: str, received_type: str):
        self.key = key
        self.expected_type = expected_type
        self.received_type = received_type
        super().__init__(
            f"Invalid type for '{key}': expected {expected_type}, got {received_type}"
        )


class InvalidRestartPolicyError(ServiceValidationError):
    """Raised when an invalid restart policy is specified"""

    def __init__(self, invalid_policy: str, valid_policies: set[str]):
        self.invalid_policy = invalid_policy
        self.valid_policies = valid_policies
        super().__init__(
            f"Invalid restart policy '{invalid_policy}'. Must be one of: {', '.join(valid_policies)}"
        )


class ServiceOperationError(ServiceError):
    """Base exception class for service operation errors"""
    pass


class ServiceNotFoundError(ServiceOperationError):
    """Raised when attempting to operate on a non-existent service"""

    def __init__(self, service_name: str):
        self.service_name = service_name
        super().__init__(f"Service '{service_name}' does not exist")


class ServiceAlreadyExistsError(ServiceOperationError):
    """Raised when attempting to add a service that already exists"""

    def __init__(self, service_name: str):
        self.service_name = service_name
        super().__init__(f"Service '{service_name}' already exists")


class ComposeFileError(Exception):
    """Base exception class for compose file-related errors"""
    pass


class ComposeFilePermissionError(ComposeFileError):
    """Raised when there are permission issues with the compose file"""

    def __init__(self, file_path: str, operation: str):
        self.file_path = file_path
        self.operation = operation
        super().__init__(f"Permission denied: cannot {operation} compose file '{file_path}'")


class DockerCommandError(Exception):
    """Base exception class for Docker command-related errors"""
    pass


class DockerNotFoundError(DockerCommandError):
    """Raised when Docker is not installed or not accessible"""

    def __init__(self):
        super().__init__("Neither 'docker compose' nor 'docker-compose' found")


class DockerCommandExecutionError(DockerCommandError):
    """Raised when a Docker command fails to execute"""

    def __init__(self, command: str, error_message: str):
        self.command = command
        self.error_message = error_message
        super().__init__(f"Docker command '{command}' failed: {error_message}")


class SetupAlreadyExistsError(Exception):
    """Raised when trying to initialize a setup that already exists"""

    def __init__(self):
        super().__init__("Cannot initialize: Services already exist in docker-compose.yml")


class SetupNotFoundError(Exception):
    """Raised when Setup does not exist"""

    def __init__(self):
        super().__init__("Cannot initialize: Services do not exist in docker-compose.yml")


class OdooAlreadyExistsError(Exception):
    """Raised when Odoo already exists"""

    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Cannot add Odoo: Odoo with name {name} already exists")
