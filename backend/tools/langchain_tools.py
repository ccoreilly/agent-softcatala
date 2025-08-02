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
            
            return result
        except Exception as e:
            if run_manager:
                await run_manager.on_tool_error(e)
            raise
    
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


# Additional LangChain tools that can be imported directly
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper


def create_search_tool():
    """Create a DuckDuckGo search tool."""
    return DuckDuckGoSearchRun()


def create_wikipedia_tool():
    """Create a Wikipedia search tool."""
    wikipedia = WikipediaAPIWrapper()
    return WikipediaQueryRun(api_wrapper=wikipedia)