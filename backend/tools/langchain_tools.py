"""LangChain-compatible tools wrapper."""

from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, Field

from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun

from .base import BaseTool as CustomBaseTool


class LangChainToolWrapper(BaseTool):
    """Wrapper to make custom tools compatible with LangChain."""
    
    name: str = Field(description="The name of the tool")
    description: str = Field(description="The description of the tool")
    custom_tool: CustomBaseTool = Field(description="The wrapped custom tool")
    
    def __init__(self, custom_tool: CustomBaseTool, **kwargs):
        """Initialize the wrapper with a custom tool.
        
        Args:
            custom_tool: The custom tool to wrap
        """
        tool_def = custom_tool.definition
        super().__init__(
            name=tool_def.name,
            description=tool_def.description,
            custom_tool=custom_tool,
            **kwargs
        )
    
    class Config:
        """Configuration for the tool."""
        arbitrary_types_allowed = True
    
    def _run(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any,
    ) -> Any:
        """Run the tool synchronously."""
        # LangChain expects sync execution, but our tools are async
        # This is a fallback that shouldn't be used in practice
        import asyncio
        return asyncio.run(self._arun(run_manager=run_manager, **kwargs))
    
    async def _arun(
        self,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
        **kwargs: Any,
    ) -> Any:
        """Run the tool asynchronously."""
        try:
            # Validate parameters
            self.custom_tool.validate_parameters(kwargs)
            
            # Execute the custom tool
            result = await self.custom_tool.execute(**kwargs)
            
            # Ensure the result indicates success/failure for agent processing
            if isinstance(result, dict):
                # If tool returned an error status, we should raise an exception
                # so the agent knows the tool failed
                if result.get("status") == "error":
                    error_msg = result.get("error", "Tool execution failed")
                    raise Exception(f"Tool {self.name} failed: {error_msg}")
                
                # For successful results, return as-is
                return result
            else:
                # For non-dict results, wrap in a structured response
                return {
                    "result": result,
                    "status": "success",
                    "tool": self.name
                }
            
        except Exception as e:
            error_details = {
                "error": str(e),
                "status": "error",
                "tool": self.name,
                "parameters": kwargs
            }
            
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Tool {self.name} execution failed: {e}")
            
            # Notify the callback manager if available
            if run_manager:
                await run_manager.on_tool_error(e)
            
            # Return structured error response instead of raising
            # This allows the agent to continue processing with error information
            return error_details
    
    @property
    def args_schema(self) -> Optional[Type[BaseModel]]:
        """Return the arguments schema for the tool."""
        # Dynamically create a Pydantic model based on tool parameters
        tool_def = self.custom_tool.definition
        
        if not tool_def.parameters:
            return None
        
        # Build fields dictionary for dynamic model
        fields = {}
        for param in tool_def.parameters:
            field_kwargs = {
                "description": param.description,
            }
            
            if not param.required:
                field_kwargs["default"] = param.default
            
            # Map parameter types to Python types
            param_type = str  # Default to string
            if param.type == "integer":
                param_type = int
            elif param.type == "number":
                param_type = float
            elif param.type == "boolean":
                param_type = bool
            elif param.type == "array":
                param_type = list
            elif param.type == "object":
                param_type = dict
            
            fields[param.name] = (param_type, Field(**field_kwargs))
        
        # Create dynamic Pydantic model
        return type(
            f"{self.name}Schema",
            (BaseModel,),
            {
                "__annotations__": {name: field_type for name, (field_type, _) in fields.items()},
                **{name: field_value for name, (_, field_value) in fields.items()}
            }
        )


