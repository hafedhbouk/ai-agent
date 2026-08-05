class AgentPlatformException(Exception):
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class AgentNotFoundError(AgentPlatformException):
    def __init__(self, agent_name: str):
        super().__init__(f"Agent '{agent_name}' not found", "AGENT_NOT_FOUND")


class DocumentNotFoundError(AgentPlatformException):
    def __init__(self, document_id: int):
        super().__init__(f"Document with id {document_id} not found", "DOCUMENT_NOT_FOUND")


class VectorStoreError(AgentPlatformException):
    def __init__(self, message: str):
        super().__init__(message, "VECTOR_STORE_ERROR")


class ToolExecutionError(AgentPlatformException):
    def __init__(self, tool_name: str, message: str):
        super().__init__(f"Tool '{tool_name}' execution failed: {message}", "TOOL_EXECUTION_ERROR")


class AuthenticationError(AgentPlatformException):
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message, "AUTHENTICATION_ERROR")


class AuthorizationError(AgentPlatformException):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, "AUTHORIZATION_ERROR")


class RateLimitError(AgentPlatformException):
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, "RATE_LIMIT_EXCEEDED")
