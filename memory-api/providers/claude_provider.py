# ABOUTME: Claude provider implementation for BETTY Multi-Agent Platform
# ABOUTME: Wraps Anthropic's Claude API with standardized interface

import asyncio
from typing import Dict, List, Any, AsyncGenerator
import anthropic
from anthropic import AsyncAnthropic
import structlog

from .base_provider import BaseProvider, ChatRequest, ChatResponse, Message, ProviderCapability

logger = structlog.get_logger(__name__)

class ClaudeProvider(BaseProvider):
    """Claude API provider implementation"""
    
    # Claude pricing (as of 2024) - costs in dollars per 1M tokens
    PRICING = {
        'claude-3-5-sonnet-20241022': {
            'input': 3.00,   # $3.00 per 1M input tokens
            'output': 15.00  # $15.00 per 1M output tokens
        },
        'claude-3-5-haiku-20241022': {
            'input': 1.00,   # $1.00 per 1M input tokens
            'output': 5.00   # $5.00 per 1M output tokens
        },
        'claude-3-opus-20240229': {
            'input': 15.00,  # $15.00 per 1M input tokens
            'output': 75.00  # $75.00 per 1M output tokens
        }
    }
    
    def __init__(self, agent_id, config, credentials):
        super().__init__(agent_id, config, credentials)
        self.client = None
        self.model = config.get('model', 'claude-3-5-sonnet-20241022')
        self.max_tokens = config.get('max_tokens', 4096)
        self.temperature = config.get('temperature', 0.7)
        
    async def initialize(self) -> bool:
        """Initialize Claude client"""
        try:
            api_key = self.credentials.get('api_key')
            if not api_key:
                raise ValueError("Claude API key not found in credentials")
                
            self.client = AsyncAnthropic(api_key=api_key)
            
            # Test connection
            await self.health_check()
            
            self.logger.info("Claude provider initialized successfully", model=self.model)
            return True
            
        except Exception as e:
            self.logger.error("Failed to initialize Claude provider", error=str(e))
            return False
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Send chat request to Claude"""
        self._validate_request(request)
        
        try:
            # Convert messages to Claude format
            claude_messages = self._convert_messages(request.messages)
            
            # Extract system message if present
            system_message = None
            if claude_messages and claude_messages[0]['role'] == 'system':
                system_message = claude_messages.pop(0)['content']
            
            # Prepare request parameters
            params = {
                'model': request.model or self.model,
                'max_tokens': request.max_tokens or self.max_tokens,
                'temperature': request.temperature or self.temperature,
                'messages': claude_messages
            }
            
            if system_message:
                params['system'] = system_message
            
            # Make API call
            response = await self.client.messages.create(**params)
            
            # Extract response content
            content = response.content[0].text if response.content else ""
            
            # Prepare usage statistics
            usage = {
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens,
                'total_tokens': response.usage.input_tokens + response.usage.output_tokens
            }
            
            self.logger.info("Claude chat completed", 
                           input_tokens=usage['input_tokens'],
                           output_tokens=usage['output_tokens'])
            
            return self._format_response(content, usage, params['model'])
            
        except Exception as e:
            self.logger.error("Claude chat failed", error=str(e))
            raise
    
    async def chat_stream(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """Stream chat response from Claude"""
        self._validate_request(request)
        
        try:
            # Convert messages to Claude format
            claude_messages = self._convert_messages(request.messages)
            
            # Extract system message if present
            system_message = None
            if claude_messages and claude_messages[0]['role'] == 'system':
                system_message = claude_messages.pop(0)['content']
            
            # Prepare request parameters
            params = {
                'model': request.model or self.model,
                'max_tokens': request.max_tokens or self.max_tokens,
                'temperature': request.temperature or self.temperature,
                'messages': claude_messages,
                'stream': True
            }
            
            if system_message:
                params['system'] = system_message
            
            # Stream response
            async with self.client.messages.stream(**params) as stream:
                async for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            self.logger.error("Claude stream failed", error=str(e))
            raise
    
    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """Convert standard messages to Claude format"""
        claude_messages = []
        
        for message in messages:
            claude_messages.append({
                'role': message.role,
                'content': message.content
            })
            
        return claude_messages
    
    async def get_capabilities(self) -> List[ProviderCapability]:
        """Get Claude's capabilities"""
        return [
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
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Claude API health"""
        try:
            # Simple test request
            test_response = await self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            
            return {
                "status": "healthy",
                "model": self.model,
                "response_time_ms": 100,  # Could measure actual response time
                "api_available": True
            }
            
        except anthropic.APIError as e:
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
        """Calculate cost in cents for Claude usage"""
        if self.model not in self.PRICING:
            return 0
            
        pricing = self.PRICING[self.model]
        
        input_cost = (usage.get('input_tokens', 0) / 1_000_000) * pricing['input']
        output_cost = (usage.get('output_tokens', 0) / 1_000_000) * pricing['output']
        
        total_cost_dollars = input_cost + output_cost
        return int(total_cost_dollars * 100)  # Convert to cents