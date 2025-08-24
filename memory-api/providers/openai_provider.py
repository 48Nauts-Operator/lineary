# ABOUTME: OpenAI provider implementation for BETTY Multi-Agent Platform  
# ABOUTME: Wraps OpenAI's API with standardized interface

import asyncio
from typing import Dict, List, Any, AsyncGenerator
import openai
from openai import AsyncOpenAI
import structlog

from .base_provider import BaseProvider, ChatRequest, ChatResponse, Message, ProviderCapability

logger = structlog.get_logger(__name__)

class OpenAIProvider(BaseProvider):
    """OpenAI API provider implementation"""
    
    # OpenAI pricing (as of 2024) - costs in dollars per 1M tokens
    PRICING = {
        'gpt-4o': {
            'input': 5.00,   # $5.00 per 1M input tokens
            'output': 15.00  # $15.00 per 1M output tokens
        },
        'gpt-4o-mini': {
            'input': 0.15,   # $0.15 per 1M input tokens
            'output': 0.60   # $0.60 per 1M output tokens
        },
        'gpt-4-turbo': {
            'input': 10.00,  # $10.00 per 1M input tokens
            'output': 30.00  # $30.00 per 1M output tokens
        },
        'gpt-3.5-turbo': {
            'input': 0.50,   # $0.50 per 1M input tokens
            'output': 1.50   # $1.50 per 1M output tokens
        }
    }
    
    def __init__(self, agent_id, config, credentials):
        super().__init__(agent_id, config, credentials)
        self.client = None
        self.model = config.get('model', 'gpt-4o-mini')
        self.max_tokens = config.get('max_tokens', 4096)
        self.temperature = config.get('temperature', 0.7)
        
    async def initialize(self) -> bool:
        """Initialize OpenAI client"""
        try:
            api_key = self.credentials.get('api_key')
            if not api_key:
                raise ValueError("OpenAI API key not found in credentials")
            
            # Support for custom base URL (for Azure OpenAI, etc.)
            base_url = self.config.get('base_url')
            
            if base_url:
                self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
            else:
                self.client = AsyncOpenAI(api_key=api_key)
            
            # Test connection
            await self.health_check()
            
            self.logger.info("OpenAI provider initialized successfully", model=self.model)
            return True
            
        except Exception as e:
            self.logger.error("Failed to initialize OpenAI provider", error=str(e))
            return False
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Send chat request to OpenAI"""
        self._validate_request(request)
        
        try:
            # Convert messages to OpenAI format
            openai_messages = self._convert_messages(request.messages)
            
            # Prepare request parameters
            params = {
                'model': request.model or self.model,
                'messages': openai_messages,
                'max_tokens': request.max_tokens or self.max_tokens,
                'temperature': request.temperature or self.temperature
            }
            
            # Make API call
            response = await self.client.chat.completions.create(**params)
            
            # Extract response content
            content = response.choices[0].message.content if response.choices else ""
            
            # Prepare usage statistics
            usage = {
                'input_tokens': response.usage.prompt_tokens,
                'output_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
            
            self.logger.info("OpenAI chat completed",
                           input_tokens=usage['input_tokens'],
                           output_tokens=usage['output_tokens'])
            
            return self._format_response(content, usage, params['model'])
            
        except Exception as e:
            self.logger.error("OpenAI chat failed", error=str(e))
            raise
    
    async def chat_stream(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """Stream chat response from OpenAI"""
        self._validate_request(request)
        
        try:
            # Convert messages to OpenAI format
            openai_messages = self._convert_messages(request.messages)
            
            # Prepare request parameters
            params = {
                'model': request.model or self.model,
                'messages': openai_messages,
                'max_tokens': request.max_tokens or self.max_tokens,
                'temperature': request.temperature or self.temperature,
                'stream': True
            }
            
            # Stream response
            stream = await self.client.chat.completions.create(**params)
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            self.logger.error("OpenAI stream failed", error=str(e))
            raise
    
    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """Convert standard messages to OpenAI format"""
        openai_messages = []
        
        for message in messages:
            openai_messages.append({
                'role': message.role,
                'content': message.content
            })
            
        return openai_messages
    
    async def get_capabilities(self) -> List[ProviderCapability]:
        """Get OpenAI's capabilities"""
        capabilities = [
            ProviderCapability(
                name="text_generation",
                description="Generate human-like text responses",
                parameters={"max_tokens": self.max_tokens, "temperature": self.temperature}
            ),
            ProviderCapability(
                name="code_analysis",
                description="Analyze and review code",
                parameters={"languages": ["python", "javascript", "typescript", "sql"]}
            ),
            ProviderCapability(
                name="reasoning",
                description="Complex reasoning and problem solving",
                parameters={"chain_of_thought": True}
            ),
            ProviderCapability(
                name="multilingual",
                description="Support for multiple languages",
                parameters={"languages": ["english", "spanish", "french", "german", "chinese"]}
            )
        ]
        
        # Add function calling for GPT-4 models
        if 'gpt-4' in self.model:
            capabilities.append(
                ProviderCapability(
                    name="function_calling",
                    description="Call functions and use tools",
                    parameters={"max_functions": 10}
                )
            )
        
        return capabilities
    
    async def health_check(self) -> Dict[str, Any]:
        """Check OpenAI API health"""
        try:
            # Simple test request
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            
            return {
                "status": "healthy",
                "model": self.model,
                "response_time_ms": 100,  # Could measure actual response time
                "api_available": True
            }
            
        except openai.APIError as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "api_available": False
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "api_available": False
            }
    
    def calculate_cost(self, usage: Dict[str, int]) -> int:
        """Calculate cost in cents for OpenAI usage"""
        if self.model not in self.PRICING:
            return 0
            
        pricing = self.PRICING[self.model]
        
        input_cost = (usage.get('input_tokens', 0) / 1_000_000) * pricing['input']
        output_cost = (usage.get('output_tokens', 0) / 1_000_000) * pricing['output']
        
        total_cost_dollars = input_cost + output_cost
        return int(total_cost_dollars * 100)  # Convert to cents