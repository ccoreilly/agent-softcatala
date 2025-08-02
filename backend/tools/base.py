from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel

class ToolParameter(BaseModel):
    """Definition of a tool parameter"""
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None

class ToolDefinition(BaseModel):
    """Tool definition for the agent"""
    name: str
    description: str
    parameters: list[ToolParameter]

class BaseTool(ABC):
    """Base class for all agent tools"""
    
    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        """Return the tool definition"""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters"""
        pass
    
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """Validate that required parameters are provided"""
        for param in self.definition.parameters:
            if param.required and param.name not in params:
                raise ValueError(f"Required parameter '{param.name}' missing for tool '{self.definition.name}'")
        return True