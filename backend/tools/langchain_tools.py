"""LangChain-compatible tools wrapper."""

import json
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
    
    def __init__(self, custom_tool: CustomBaseTool, use_catalan: bool = False, **kwargs):
        """Initialize the wrapper with a custom tool.
        
        Args:
            custom_tool: The custom tool to wrap
            use_catalan: Whether to use Catalan tool descriptions
        """
        # Use Catalan definition if available and requested
        if use_catalan and hasattr(custom_tool, 'catalan_definition'):
            tool_def = custom_tool.catalan_definition
        else:
            tool_def = custom_tool.definition
        
        # Generate the schema before calling super()
        schema = self._generate_args_schema(custom_tool, use_catalan)
        
        super().__init__(
            name=tool_def.name,
            description=tool_def.description,
            custom_tool=custom_tool,
            args_schema=schema,  # Set the schema explicitly
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
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🔧 TOOL EXECUTION STARTED: {self.name}")
        logger.info(f"🔧 Tool description: {self.description}")
        logger.info(f"🔧 Tool parameters: {json.dumps(kwargs, indent=2, ensure_ascii=False)}")
        logger.info(f"🔧 Run manager: {run_manager}")
        
        # Log detailed parameter information
        if hasattr(self.custom_tool, 'definition'):
            definition = self.custom_tool.definition
            logger.info(f"🔧 Tool definition name: {definition.name}")
            logger.info(f"🔧 Tool definition description: {definition.description}")
            if definition.parameters:
                logger.info(f"🔧 Expected parameters: {[p.name for p in definition.parameters]}")
                for param in definition.parameters:
                    param_value = kwargs.get(param.name, 'NOT_PROVIDED')
                    logger.info(f"🔧   - {param.name} ({param.type}): {param_value}")
        
        try:
            # Validate parameters
            logger.debug(f"🔧 Validating parameters for {self.name}")
            self.custom_tool.validate_parameters(kwargs)
            logger.debug(f"🔧 Parameter validation successful for {self.name}")
            
            # Execute the custom tool
            logger.info(f"🔧 Executing custom tool: {self.name}")
            result = await self.custom_tool.execute(**kwargs)
            logger.info(f"🔧 Tool execution completed: {self.name}")
            
            # Log the complete result structure
            result_log = {
                "tool_name": self.name,
                "result_type": type(result).__name__,
                "result_content": result,
                "success": True
            }
            logger.info(f"🔧 COMPLETE TOOL RESULT: {json.dumps(result_log, indent=2, ensure_ascii=False)}")
            
            # Ensure the result indicates success/failure for agent processing
            if isinstance(result, dict):
                # If tool returned an error status, we should raise an exception
                # so the agent knows the tool failed
                if result.get("status") == "error":
                    error_msg = result.get("error", "Tool execution failed")
                    logger.error(f"🔧 Tool {self.name} returned error status: {error_msg}")
                    raise Exception(f"Tool {self.name} failed: {error_msg}")
                
                # For successful results, return as-is
                logger.info(f"🔧 Tool {self.name} execution successful")
                return result
            else:
                # For non-dict results, wrap in a structured response
                wrapped_result = {
                    "result": result,
                    "status": "success",
                    "tool": self.name
                }
                logger.info(f"🔧 Tool {self.name} result wrapped: {wrapped_result}")
                return wrapped_result
            
        except Exception as e:
            error_details = {
                "error": str(e),
                "status": "error",
                "tool": self.name,
                "parameters": kwargs
            }
            
            # Log the error for debugging
            logger.error(f"🔧 Tool {self.name} execution failed: {e}")
            logger.exception(f"🔧 Full error traceback for {self.name}:")
            
            # Notify the callback manager if available
            if run_manager:
                logger.debug(f"🔧 Notifying run manager of error for {self.name}")
                await run_manager.on_tool_error(e)
            
            # Return structured error response instead of raising
            # This allows the agent to continue processing with error information
            logger.info(f"🔧 Returning error details for {self.name}: {error_details}")
            return error_details
    
    def _generate_args_schema(self, custom_tool: CustomBaseTool, use_catalan: bool = False) -> Optional[Type[BaseModel]]:
        """Generate the arguments schema for the tool during initialization."""
        import logging
        logger = logging.getLogger(__name__)
        
        # Dynamically create a Pydantic model based on tool parameters
        # Use Catalan definition if available and requested
        if use_catalan and hasattr(custom_tool, 'catalan_definition'):
            tool_def = custom_tool.catalan_definition
        else:
            tool_def = custom_tool.definition
        
        if not tool_def.parameters:
            return None
        
        # Build fields dictionary for dynamic model
        fields = {}
        annotations = {}
        
        for param in tool_def.parameters:
            field_kwargs = {
                "description": param.description,
            }
            
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
            
            # Handle optional parameters properly
            if not param.required:
                if param.default is not None:
                    field_kwargs["default"] = param.default
                else:
                    field_kwargs["default"] = None
                # Make type optional
                from typing import Optional
                param_type = Optional[param_type]
            
            # Store field info
            annotations[param.name] = param_type
            fields[param.name] = Field(**field_kwargs)
        
        try:
            # Create dynamic Pydantic model class
            schema_class = type(
                f"{tool_def.name}Schema",
                (BaseModel,),
                {
                    "__annotations__": annotations,
                    **fields
                }
            )
            
            logger.debug(f"🔧 Generated schema for {tool_def.name}: {schema_class}")
            return schema_class
        except Exception as e:
            logger.error(f"🔧 Failed to create schema for {tool_def.name}: {e}")
            logger.exception(f"🔧 Schema creation exception:")
            return None


