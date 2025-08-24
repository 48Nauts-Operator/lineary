# ABOUTME: Base provider interface for BETTY Multi-Agent Platform
# ABOUTME: Defines common interface that all agent providers must implement

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncGenerator
from uuid import UUID
import structlog
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

class Message(BaseModel):
    """Standard message format across all providers"""
    role: str  # 'user', 'assistant', 'system'
    content: str
    metadata: Dict[str, Any] = {}

class ChatRequest(BaseModel):
    """Standard chat request format"""
    messages: List[Message]
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    model: Optional[str] = None
    stream: bool = False
    metadata: Dict[str, Any] = {}

class ChatResponse(BaseModel):
    """Standard chat response format"""
    message: Message
    usage: Dict[str, int] = {}  # token usage stats
    model: str
    cost_cents: int = 0
    metadata: Dict[str, Any] = {}

class ProviderCapability(BaseModel):
    """Provider capability definition"""
    name: str
    description: str
    parameters: Dict[str, Any] = {}
    supported: bool = True

class BaseProvider(ABC):
    """Base class for all agent providers"""
    
    def __init__(self, agent_id: UUID, config: Dict[str, Any], credentials: Dict[str, str]):
        self.agent_id = agent_id
        self.config = config
        self.credentials = credentials
        self.logger = logger.bind(agent_id=str(agent_id), provider=self.__class__.__name__)
        
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the provider with credentials and config"""
        pass
        
    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Send a chat request and get response"""
        pass
        
    @abstractmethod
    async def chat_stream(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """Send a chat request and stream response"""
        pass
        
    @abstractmethod
    async def get_capabilities(self) -> List[ProviderCapability]:
        """Get list of capabilities this provider supports"""
        pass
        
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check if the provider is healthy and available"""
        pass
        
    @abstractmethod
    def calculate_cost(self, usage: Dict[str, int]) -> int:
        """Calculate cost in cents based on token usage"""
        pass
        
    async def cleanup(self):
        """Cleanup resources when provider is stopped"""
        pass
    
    def _validate_request(self, request: ChatRequest) -> bool:
        """Validate chat request format"""
        if not request.messages:
            raise ValueError("Chat request must contain at least one message")
            
        for message in request.messages:
            if message.role not in ['user', 'assistant', 'system']:
                raise ValueError(f"Invalid message role: {message.role}")
                
        return True
    
    def _format_response(self, content: str, usage: Dict[str, int], model: str) -> ChatResponse:
        """Format response in standard format"""
        return ChatResponse(
            message=Message(role='assistant', content=content),
            usage=usage,
            model=model,
            cost_cents=self.calculate_cost(usage),
            metadata={"provider": self.__class__.__name__}
        )