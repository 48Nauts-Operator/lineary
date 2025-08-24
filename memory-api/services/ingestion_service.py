# ABOUTME: Comprehensive ingestion service for BETTY Memory System
# ABOUTME: Processes all Claude interactions into temporal knowledge graphs and searchable memory

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID, uuid4
import structlog

from models.ingestion import (
    ConversationIngestionRequest,
    CodeChangeIngestionRequest,
    DecisionIngestionRequest, 
    ProblemSolutionIngestionRequest,
    ToolUsageIngestionRequest,
    BatchIngestionRequest,
    BatchIngestionResponse,
    IngestionResult,
    MessageRole,
    OutcomeType,
    ChangeCategory,
    DecisionType,
    ProblemCategory,
    ToolType
)
from models.knowledge import KnowledgeItemCreate, KnowledgeType, SourceType, ConfidenceLevel
from core.dependencies import DatabaseDependencies
from services.knowledge_service import KnowledgeService
from services.graphiti_service import GraphitiService
from services.vector_service import VectorService

logger = structlog.get_logger(__name__)

class IngestionService:
    """Comprehensive service for ingesting all Claude session data"""
    
    def __init__(self, databases: DatabaseDependencies):
        self.databases = databases
        self.knowledge_service = KnowledgeService(databases)
        self.graphiti_service = GraphitiService(databases)
        self.vector_service = VectorService(databases)
    
    async def ingest_conversation(self, request: ConversationIngestionRequest) -> IngestionResult:
        """Ingest a complete Claude conversation"""
        start_time = time.time()
        knowledge_items_created = 0
        entities_extracted = 0
        relationships_created = 0
        embeddings_generated = 0
        
        try:
            # 1. Create primary conversation knowledge item
            conversation_item = await self._create_conversation_knowledge_item(request)
            knowledge_items_created += 1
            
            # 2. Create individual message items for important messages
            message_items = await self._create_message_knowledge_items(request)
            knowledge_items_created += len(message_items)
            
            # 3. Extract and create decision items from conversation
            decision_items = await self._extract_decisions_from_conversation(request)
            knowledge_items_created += len(decision_items)
            
            # 4. Extract technical insights
            insight_items = await self._extract_technical_insights(request)
            knowledge_items_created += len(insight_items)
            
            # 5. Generate embeddings for all created items
            all_items = [conversation_item] + message_items + decision_items + insight_items
            for item in all_items:
                if item and item.id:
                    await self.vector_service.generate_and_store_embedding(
                        str(item.id),
                        f"{item.title}\n{item.content}",
                        "knowledge",
                        {
                            "knowledge_type": item.knowledge_type,
                            "session_id": str(request.session_id),
                            "project_id": request.project_id
                        }
                    )
                    embeddings_generated += 1
            
            # 6. Add to Graphiti temporal knowledge graph
            episode_data = self._prepare_conversation_episode_data(request, all_items)
            graphiti_result = await self.graphiti_service.add_episode(episode_data)
            
            if graphiti_result:
                entities_extracted = len(graphiti_result.get("entities", []))
                relationships_created = len(graphiti_result.get("relationships", []))
            
            processing_time = (time.time() - start_time) * 1000
            
            logger.info(
                "Conversation ingested successfully",
                session_id=str(request.session_id),
                knowledge_items=knowledge_items_created,
                entities=entities_extracted,
                relationships=relationships_created,
                processing_time_ms=processing_time
            )
            
            return IngestionResult(
                success=True,
                item_id=conversation_item.id if conversation_item else None,
                knowledge_items_created=knowledge_items_created,
                entities_extracted=entities_extracted,
                relationships_created=relationships_created,
                embeddings_generated=embeddings_generated,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(
                "Failed to ingest conversation",
                session_id=str(request.session_id),
                error=str(e)
            )
            return IngestionResult(
                success=False,
                error_message=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    async def ingest_code_change(self, request: CodeChangeIngestionRequest) -> IngestionResult:
        """Ingest code changes from Claude tools"""
        start_time = time.time()
        knowledge_items_created = 0
        entities_extracted = 0
        relationships_created = 0
        embeddings_generated = 0
        
        try:
            # 1. Create main code change knowledge item
            code_change_item = await self._create_code_change_knowledge_item(request)
            knowledge_items_created += 1
            
            # 2. Create individual file change items
            file_change_items = await self._create_file_change_knowledge_items(request)
            knowledge_items_created += len(file_change_items)
            
            # 3. Extract patterns and architectural insights
            pattern_items = await self._extract_code_patterns(request)
            knowledge_items_created += len(pattern_items)
            
            # 4. Generate embeddings
            all_items = [code_change_item] + file_change_items + pattern_items
            for item in all_items:
                if item and item.id:
                    await self.vector_service.generate_and_store_embedding(
                        str(item.id),
                        f"{item.title}\n{item.content}",
                        "knowledge",
                        {
                            "knowledge_type": item.knowledge_type,
                            "session_id": str(request.session_id),
                            "project_id": request.project_id,
                            "tool_used": request.code_change_data.tool_used
                        }
                    )
                    embeddings_generated += 1
            
            # 5. Add to Graphiti
            episode_data = self._prepare_code_change_episode_data(request, all_items)
            graphiti_result = await self.graphiti_service.add_episode(episode_data)
            
            if graphiti_result:
                entities_extracted = len(graphiti_result.get("entities", []))
                relationships_created = len(graphiti_result.get("relationships", []))
            
            processing_time = (time.time() - start_time) * 1000
            
            return IngestionResult(
                success=True,
                item_id=code_change_item.id if code_change_item else None,
                knowledge_items_created=knowledge_items_created,
                entities_extracted=entities_extracted,
                relationships_created=relationships_created,
                embeddings_generated=embeddings_generated,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(
                "Failed to ingest code change",
                session_id=str(request.session_id),
                error=str(e)
            )
            return IngestionResult(
                success=False,
                error_message=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    async def ingest_decision(self, request: DecisionIngestionRequest) -> IngestionResult:
        """Ingest architectural or technical decisions"""
        start_time = time.time()
        knowledge_items_created = 0
        entities_extracted = 0
        relationships_created = 0
        embeddings_generated = 0
        
        try:
            # 1. Create main decision knowledge item
            decision_item = await self._create_decision_knowledge_item(request)
            knowledge_items_created += 1
            
            # 2. Create alternative analysis items
            alternative_items = await self._create_alternative_analysis_items(request)
            knowledge_items_created += len(alternative_items)
            
            # 3. Generate embeddings
            all_items = [decision_item] + alternative_items
            for item in all_items:
                if item and item.id:
                    await self.vector_service.generate_and_store_embedding(
                        str(item.id),
                        f"{item.title}\n{item.content}",
                        "knowledge",
                        {
                            "knowledge_type": item.knowledge_type,
                            "project_id": request.project_id,
                            "decision_type": request.decision_data.decision_type
                        }
                    )
                    embeddings_generated += 1
            
            # 4. Add to Graphiti
            episode_data = self._prepare_decision_episode_data(request, all_items)
            graphiti_result = await self.graphiti_service.add_episode(episode_data)
            
            if graphiti_result:
                entities_extracted = len(graphiti_result.get("entities", []))
                relationships_created = len(graphiti_result.get("relationships", []))
            
            processing_time = (time.time() - start_time) * 1000
            
            return IngestionResult(
                success=True,
                item_id=decision_item.id if decision_item else None,
                knowledge_items_created=knowledge_items_created,
                entities_extracted=entities_extracted,
                relationships_created=relationships_created,
                embeddings_generated=embeddings_generated,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(
                "Failed to ingest decision",
                decision_title=request.decision_data.title,
                error=str(e)
            )
            return IngestionResult(
                success=False,
                error_message=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    async def ingest_problem_solution(self, request: ProblemSolutionIngestionRequest) -> IngestionResult:
        """Ingest problem-solution pairs"""
        start_time = time.time()
        knowledge_items_created = 0
        entities_extracted = 0
        relationships_created = 0
        embeddings_generated = 0
        
        try:
            # 1. Create problem knowledge item
            problem_item = await self._create_problem_knowledge_item(request)
            knowledge_items_created += 1
            
            # 2. Create solution knowledge item
            solution_item = await self._create_solution_knowledge_item(request)
            knowledge_items_created += 1
            
            # 3. Create verification/testing items
            verification_items = await self._create_verification_knowledge_items(request)
            knowledge_items_created += len(verification_items)
            
            # 4. Generate embeddings
            all_items = [problem_item, solution_item] + verification_items
            for item in all_items:
                if item and item.id:
                    await self.vector_service.generate_and_store_embedding(
                        str(item.id),
                        f"{item.title}\n{item.content}",
                        "knowledge",
                        {
                            "knowledge_type": item.knowledge_type,
                            "project_id": request.project_id,
                            "problem_category": request.problem_solution_data.problem.category
                        }
                    )
                    embeddings_generated += 1
            
            # 5. Add to Graphiti
            episode_data = self._prepare_problem_solution_episode_data(request, all_items)
            graphiti_result = await self.graphiti_service.add_episode(episode_data)
            
            if graphiti_result:
                entities_extracted = len(graphiti_result.get("entities", []))
                relationships_created = len(graphiti_result.get("relationships", []))
            
            processing_time = (time.time() - start_time) * 1000
            
            return IngestionResult(
                success=True,
                item_id=problem_item.id if problem_item else None,
                knowledge_items_created=knowledge_items_created,
                entities_extracted=entities_extracted,
                relationships_created=relationships_created,
                embeddings_generated=embeddings_generated,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(
                "Failed to ingest problem-solution",
                problem_title=request.problem_solution_data.problem.title,
                error=str(e)
            )
            return IngestionResult(
                success=False,
                error_message=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    async def ingest_tool_usage(self, request: ToolUsageIngestionRequest) -> IngestionResult:
        """Ingest Claude tool usage for pattern analysis"""
        start_time = time.time()
        knowledge_items_created = 0
        entities_extracted = 0
        relationships_created = 0
        embeddings_generated = 0
        
        try:
            # 1. Create tool usage knowledge item
            tool_item = await self._create_tool_usage_knowledge_item(request)
            knowledge_items_created += 1
            
            # 2. Generate embedding
            if tool_item and tool_item.id:
                await self.vector_service.generate_and_store_embedding(
                    str(tool_item.id),
                    f"{tool_item.title}\n{tool_item.content}",
                    "knowledge",
                    {
                        "knowledge_type": tool_item.knowledge_type,
                        "session_id": str(request.session_id),
                        "project_id": request.project_id,
                        "tool_name": request.tool_usage_data.tool_name,
                        "success": request.tool_usage_data.result.success
                    }
                )
                embeddings_generated += 1
            
            # 3. Add to Graphiti (for important tools only)
            if request.tool_usage_data.tool_name in [ToolType.WRITE, ToolType.EDIT, ToolType.MULTIEDIT]:
                episode_data = self._prepare_tool_usage_episode_data(request, [tool_item])
                graphiti_result = await self.graphiti_service.add_episode(episode_data)
                
                if graphiti_result:
                    entities_extracted = len(graphiti_result.get("entities", []))
                    relationships_created = len(graphiti_result.get("relationships", []))
            
            processing_time = (time.time() - start_time) * 1000
            
            return IngestionResult(
                success=True,
                item_id=tool_item.id if tool_item else None,
                knowledge_items_created=knowledge_items_created,
                entities_extracted=entities_extracted,
                relationships_created=relationships_created,
                embeddings_generated=embeddings_generated,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(
                "Failed to ingest tool usage",
                session_id=str(request.session_id),
                tool_name=request.tool_usage_data.tool_name,
                error=str(e)
            )
            return IngestionResult(
                success=False,
                error_message=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    async def batch_ingest(
        self, 
        request: BatchIngestionRequest, 
        batch_id: UUID
    ) -> BatchIngestionResponse:
        """Process batch ingestion of multiple items"""
        start_time = time.time()
        
        response = BatchIngestionResponse(
            message="Batch ingestion processing completed",
            total_items=0,
            successful_items=0,
            failed_items=0,
            batch_id=batch_id,
            errors=[]
        )
        
        try:
            # Process all item types concurrently for better performance
            tasks = []
            
            # Conversations
            for conv_req in request.conversations:
                tasks.append(("conversation", self.ingest_conversation(conv_req)))
            
            # Code changes
            for code_req in request.code_changes:
                tasks.append(("code_change", self.ingest_code_change(code_req)))
            
            # Decisions
            for decision_req in request.decisions:
                tasks.append(("decision", self.ingest_decision(decision_req)))
            
            # Problem-solutions
            for ps_req in request.problem_solutions:
                tasks.append(("problem_solution", self.ingest_problem_solution(ps_req)))
            
            # Tool usages
            for tool_req in request.tool_usages:
                tasks.append(("tool_usage", self.ingest_tool_usage(tool_req)))
            
            response.total_items = len(tasks)
            
            # Execute all tasks concurrently
            if tasks:
                results = await asyncio.gather(
                    *[task[1] for task in tasks],
                    return_exceptions=True
                )
                
                # Process results
                for i, (item_type, result) in enumerate(zip([task[0] for task in tasks], results)):
                    if isinstance(result, Exception):
                        response.failed_items += 1
                        response.errors.append({
                            "item_type": item_type,
                            "index": i,
                            "error": str(result)
                        })
                    elif isinstance(result, IngestionResult):
                        if result.success:
                            response.successful_items += 1
                            response.total_knowledge_items_created += result.knowledge_items_created
                            response.total_entities_extracted += result.entities_extracted
                            response.total_relationships_created += result.relationships_created
                            response.total_embeddings_generated += result.embeddings_generated
                            
                            # Add to appropriate result list
                            if item_type == "conversation":
                                response.conversation_results.append(result)
                            elif item_type == "code_change":
                                response.code_change_results.append(result)
                            elif item_type == "decision":
                                response.decision_results.append(result)
                            elif item_type == "problem_solution":
                                response.problem_solution_results.append(result)
                            elif item_type == "tool_usage":
                                response.tool_usage_results.append(result)
                        else:
                            response.failed_items += 1
                            response.errors.append({
                                "item_type": item_type,
                                "index": i,
                                "error": result.error_message
                            })
            
            # Store batch status in PostgreSQL for tracking
            await self._store_batch_status(batch_id, request, response)
            
            logger.info(
                "Batch ingestion completed",
                batch_id=str(batch_id),
                total_items=response.total_items,
                successful_items=response.successful_items,
                failed_items=response.failed_items,
                processing_time_ms=(time.time() - start_time) * 1000
            )
            
            return response
            
        except Exception as e:
            logger.error(
                "Failed to process batch ingestion",
                batch_id=str(batch_id),
                error=str(e)
            )
            response.failed_items = response.total_items
            response.successful_items = 0
            response.errors.append({
                "item_type": "batch",
                "error": str(e)
            })
            return response
    
    # Private helper methods for creating knowledge items
    
    async def _create_conversation_knowledge_item(self, request: ConversationIngestionRequest):
        """Create main conversation knowledge item"""
        content_parts = []
        
        # Build comprehensive content from all messages
        for msg in request.conversation_data.messages:
            role_label = msg.role.value.upper()
            content_parts.append(f"{role_label}: {msg.content[:1000]}")  # Limit per message
        
        # Add summary and outcomes
        if request.conversation_data.summary:
            content_parts.append(f"\nSUMMARY: {request.conversation_data.summary}")
        
        if request.conversation_data.key_decisions:
            content_parts.append(f"\nKEY DECISIONS: {'; '.join(request.conversation_data.key_decisions)}")
        
        if request.conversation_data.lessons_learned:
            content_parts.append(f"\nLESSONS LEARNED: {'; '.join(request.conversation_data.lessons_learned)}")
        
        content = "\n\n".join(content_parts)
        
        # Create knowledge item
        knowledge_item = KnowledgeItemCreate(
            title=f"Claude Conversation - {request.project_id} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            content=content,
            knowledge_type=KnowledgeType.CONVERSATION,
            source_type=SourceType.CHAT,
            tags=[
                "conversation",
                "claude_session",
                request.project_id,
                request.conversation_data.outcome.value
            ] + request.conversation_data.technologies_used[:10],  # Limit tags
            summary=request.conversation_data.summary,
            confidence=ConfidenceLevel.HIGH if request.conversation_data.outcome == OutcomeType.SUCCESSFUL else ConfidenceLevel.MEDIUM,
            session_id=request.session_id,
            user_id=request.user_id,
            project_id=request.project_id,
            metadata={
                "outcome": request.conversation_data.outcome.value,
                "message_count": len(request.conversation_data.messages),
                "technologies_used": request.conversation_data.technologies_used,
                "patterns_applied": request.conversation_data.patterns_applied,
                "claude_version": request.claude_version,
                "environment": request.environment,
                "duration_minutes": request.duration_minutes
            }
        )
        
        return await self.knowledge_service.create_knowledge_item(knowledge_item)
    
    async def _create_message_knowledge_items(self, request: ConversationIngestionRequest):
        """Create knowledge items for important individual messages"""
        items = []
        
        for i, msg in enumerate(request.conversation_data.messages):
            # Only create items for messages with significant context or that are long
            if (msg.context and 
                (msg.context.user_intent or msg.context.problem_category or 
                 msg.context.files_mentioned or msg.context.technologies_mentioned) 
                or len(msg.content) > 500):
                
                tags = ["message", msg.role.value, request.project_id]
                
                if msg.context:
                    if msg.context.problem_category:
                        tags.append(msg.context.problem_category.value)
                    tags.extend(msg.context.technologies_mentioned[:5])
                
                knowledge_item = KnowledgeItemCreate(
                    title=f"Message {i+1} - {msg.role.value} - {request.project_id}",
                    content=msg.content,
                    knowledge_type=KnowledgeType.CONVERSATION,
                    source_type=SourceType.CHAT,
                    tags=tags,
                    summary=msg.context.user_intent if msg.context else None,
                    confidence=ConfidenceLevel.MEDIUM,
                    session_id=request.session_id,
                    user_id=request.user_id,
                    project_id=request.project_id,
                    metadata={
                        "message_index": i,
                        "role": msg.role.value,
                        "timestamp": msg.timestamp.isoformat(),
                        "context": msg.context.dict() if msg.context else None,
                        "tool_calls": msg.tool_calls
                    }
                )
                
                item = await self.knowledge_service.create_knowledge_item(knowledge_item)
                if item:
                    items.append(item)
        
        return items
    
    async def _extract_decisions_from_conversation(self, request: ConversationIngestionRequest):
        """Extract decision items from conversation content"""
        items = []
        
        if request.conversation_data.key_decisions:
            for i, decision in enumerate(request.conversation_data.key_decisions):
                knowledge_item = KnowledgeItemCreate(
                    title=f"Decision: {decision[:100]}",
                    content=f"Decision made during conversation: {decision}",
                    knowledge_type=KnowledgeType.INSIGHT,
                    source_type=SourceType.CHAT,
                    tags=["decision", "conversation_decision", request.project_id],
                    summary=decision,
                    confidence=ConfidenceLevel.HIGH,
                    session_id=request.session_id,
                    user_id=request.user_id,
                    project_id=request.project_id,
                    metadata={
                        "decision_index": i,
                        "extracted_from": "conversation",
                        "conversation_outcome": request.conversation_data.outcome.value
                    }
                )
                
                item = await self.knowledge_service.create_knowledge_item(knowledge_item)
                if item:
                    items.append(item)
        
        return items
    
    async def _extract_technical_insights(self, request: ConversationIngestionRequest):
        """Extract technical insights from conversation"""
        items = []
        
        if request.conversation_data.lessons_learned:
            for i, lesson in enumerate(request.conversation_data.lessons_learned):
                knowledge_item = KnowledgeItemCreate(
                    title=f"Technical Insight: {lesson[:100]}",
                    content=f"Lesson learned: {lesson}",
                    knowledge_type=KnowledgeType.INSIGHT,
                    source_type=SourceType.CHAT,
                    tags=["insight", "lesson_learned", request.project_id] + request.conversation_data.technologies_used[:5],
                    summary=lesson,
                    confidence=ConfidenceLevel.HIGH,
                    session_id=request.session_id,
                    user_id=request.user_id,
                    project_id=request.project_id,
                    metadata={
                        "insight_index": i,
                        "extracted_from": "conversation",
                        "technologies_involved": request.conversation_data.technologies_used,
                        "patterns_applied": request.conversation_data.patterns_applied
                    }
                )
                
                item = await self.knowledge_service.create_knowledge_item(knowledge_item)
                if item:
                    items.append(item)
        
        return items
    
    async def _create_code_change_knowledge_item(self, request: CodeChangeIngestionRequest):
        """Create main code change knowledge item"""
        content_parts = []
        
        # Tool and context
        content_parts.append(f"Tool Used: {request.code_change_data.tool_used.value}")
        
        # File changes summary
        content_parts.append(f"Files Modified: {len(request.code_change_data.files_modified)}")
        
        for file_change in request.code_change_data.files_modified:
            file_summary = f"- {file_change.file_path} ({file_change.operation.value})"
            if file_change.change_intent:
                file_summary += f": {file_change.change_intent}"
            content_parts.append(file_summary)
        
        # Technical context
        if request.code_change_data.technical_context.frameworks_used:
            content_parts.append(f"Frameworks: {', '.join(request.code_change_data.technical_context.frameworks_used)}")
        
        if request.code_change_data.technical_context.patterns_applied:
            content_parts.append(f"Patterns: {', '.join(request.code_change_data.technical_context.patterns_applied)}")
        
        # Success indicators
        if request.code_change_data.success_indicators:
            content_parts.append(f"Success Indicators: {', '.join(request.code_change_data.success_indicators)}")
        
        # Error messages if any
        if request.code_change_data.error_messages:
            content_parts.append(f"Errors: {', '.join(request.code_change_data.error_messages)}")
        
        content = "\n".join(content_parts)
        
        # Determine change category for tagging
        primary_category = None
        if request.code_change_data.files_modified:
            primary_category = request.code_change_data.files_modified[0].change_category
        
        tags = [
            "code_change",
            request.code_change_data.tool_used.value.lower(),
            request.project_id
        ]
        
        if primary_category:
            tags.append(primary_category.value)
        
        tags.extend(request.code_change_data.technical_context.frameworks_used[:5])
        
        knowledge_item = KnowledgeItemCreate(
            title=f"Code Change - {request.code_change_data.tool_used.value} - {request.project_id}",
            content=content,
            knowledge_type=KnowledgeType.CODE,
            source_type=SourceType.API,
            tags=tags,
            summary=f"Modified {len(request.code_change_data.files_modified)} files using {request.code_change_data.tool_used.value}",
            confidence=ConfidenceLevel.HIGH if request.code_change_data.success_indicators else ConfidenceLevel.MEDIUM,
            session_id=request.session_id,
            user_id=request.user_id,
            project_id=request.project_id,
            metadata={
                "tool_used": request.code_change_data.tool_used.value,
                "files_count": len(request.code_change_data.files_modified),
                "technical_context": request.code_change_data.technical_context.dict(),
                "success_indicators": request.code_change_data.success_indicators,
                "error_messages": request.code_change_data.error_messages,
                "change_sequence": request.change_sequence,
                "part_of_conversation": request.part_of_conversation
            }
        )
        
        return await self.knowledge_service.create_knowledge_item(knowledge_item)
    
    async def _create_file_change_knowledge_items(self, request: CodeChangeIngestionRequest):
        """Create knowledge items for individual file changes"""
        items = []
        
        for file_change in request.code_change_data.files_modified:
            # Skip simple read operations unless they're part of complex analysis
            if file_change.operation == OperationType.READ and not file_change.change_intent:
                continue
            
            content_parts = [
                f"Operation: {file_change.operation.value}",
                f"File: {file_change.file_path}"
            ]
            
            if file_change.change_intent:
                content_parts.append(f"Intent: {file_change.change_intent}")
            
            if file_change.lines_changed:
                lines_summary = []
                for change_type, count in file_change.lines_changed.items():
                    if count > 0:
                        lines_summary.append(f"{count} {change_type}")
                if lines_summary:
                    content_parts.append(f"Changes: {', '.join(lines_summary)}")
            
            if file_change.code_snippet:
                content_parts.append(f"Code Snippet:\n{file_change.code_snippet}")
            
            content = "\n".join(content_parts)
            
            tags = [
                "file_change",
                file_change.operation.value,
                request.project_id,
                # Extract file extension for additional context
                file_change.file_path.split('.')[-1] if '.' in file_change.file_path else "no_extension"
            ]
            
            if file_change.change_category:
                tags.append(file_change.change_category.value)
            
            knowledge_item = KnowledgeItemCreate(
                title=f"File Change: {file_change.file_path.split('/')[-1]} - {file_change.operation.value}",
                content=content,
                knowledge_type=KnowledgeType.CODE,
                source_type=SourceType.API,
                tags=tags,
                summary=file_change.change_intent,
                confidence=ConfidenceLevel.HIGH,
                session_id=request.session_id,
                user_id=request.user_id,
                project_id=request.project_id,
                metadata={
                    "file_path": file_change.file_path,
                    "operation": file_change.operation.value,
                    "lines_changed": file_change.lines_changed,
                    "change_category": file_change.change_category.value if file_change.change_category else None,
                    "tool_used": request.code_change_data.tool_used.value
                }
            )
            
            item = await self.knowledge_service.create_knowledge_item(knowledge_item)
            if item:
                items.append(item)
        
        return items
    
    async def _extract_code_patterns(self, request: CodeChangeIngestionRequest):
        """Extract patterns and architectural insights from code changes"""
        items = []
        
        # Extract patterns from technical context
        for pattern in request.code_change_data.technical_context.patterns_applied:
            knowledge_item = KnowledgeItemCreate(
                title=f"Pattern Applied: {pattern}",
                content=f"Applied pattern '{pattern}' in {request.project_id} using {request.code_change_data.tool_used.value}",
                knowledge_type=KnowledgeType.INSIGHT,
                source_type=SourceType.API,
                tags=["pattern", "architecture", pattern.lower().replace(" ", "_"), request.project_id],
                summary=f"Pattern application: {pattern}",
                confidence=ConfidenceLevel.HIGH,
                session_id=request.session_id,
                user_id=request.user_id,
                project_id=request.project_id,
                metadata={
                    "pattern_name": pattern,
                    "applied_via": request.code_change_data.tool_used.value,
                    "frameworks_involved": request.code_change_data.technical_context.frameworks_used,
                    "files_affected": [fc.file_path for fc in request.code_change_data.files_modified]
                }
            )
            
            item = await self.knowledge_service.create_knowledge_item(knowledge_item)
            if item:
                items.append(item)
        
        return items
    
    async def _create_decision_knowledge_item(self, request: DecisionIngestionRequest):
        """Create main decision knowledge item"""
        content_parts = [
            f"Decision Type: {request.decision_data.decision_type.value}",
            f"Context: {request.decision_data.context}",
            f"Final Decision: {request.decision_data.final_decision}"
        ]
        
        # Add alternatives analysis
        if request.decision_data.alternatives_considered:
            content_parts.append("\nAlternatives Considered:")
            for i, alt in enumerate(request.decision_data.alternatives_considered):
                alt_text = f"- {alt.option}"
                if alt.pros:
                    alt_text += f" (Pros: {', '.join(alt.pros[:3])})"
                if alt.cons:
                    alt_text += f" (Cons: {', '.join(alt.cons[:3])})"
                content_parts.append(alt_text)
        
        # Add rationale
        if request.decision_data.rationale:
            content_parts.append(f"\nRationale: {'; '.join(request.decision_data.rationale)}")
        
        # Add implementation plan
        if request.decision_data.implementation_plan:
            content_parts.append(f"\nImplementation: {'; '.join(request.decision_data.implementation_plan)}")
        
        content = "\n".join(content_parts)
        
        tags = [
            "decision",
            request.decision_data.decision_type.value,
            request.project_id
        ]
        
        knowledge_item = KnowledgeItemCreate(
            title=request.decision_data.title,
            content=content,
            knowledge_type=KnowledgeType.INSIGHT,
            source_type=SourceType.USER_INPUT,
            tags=tags,
            summary=f"{request.decision_data.decision_type.value}: {request.decision_data.final_decision}",
            confidence=ConfidenceLevel.HIGH,
            session_id=request.session_id,
            user_id=request.user_id,
            project_id=request.project_id,
            metadata={
                "decision_type": request.decision_data.decision_type.value,
                "alternatives_count": len(request.decision_data.alternatives_considered),
                "rationale": request.decision_data.rationale,
                "implementation_plan": request.decision_data.implementation_plan,
                "success_criteria": request.decision_data.success_criteria,
                "risks_identified": request.decision_data.risks_identified,
                "triggered_by": request.triggered_by,
                "stakeholders": request.stakeholders
            }
        )
        
        return await self.knowledge_service.create_knowledge_item(knowledge_item)
    
    async def _create_alternative_analysis_items(self, request: DecisionIngestionRequest):
        """Create knowledge items for decision alternatives analysis"""
        items = []
        
        for i, alt in enumerate(request.decision_data.alternatives_considered):
            if len(alt.pros) > 2 or len(alt.cons) > 2:  # Only create items for well-analyzed alternatives
                content_parts = [
                    f"Alternative: {alt.option}",
                    f"Decision Context: {request.decision_data.title}"
                ]
                
                if alt.pros:
                    content_parts.append(f"Advantages: {'; '.join(alt.pros)}")
                
                if alt.cons:
                    content_parts.append(f"Disadvantages: {'; '.join(alt.cons)}")
                
                if alt.feasibility_score is not None:
                    content_parts.append(f"Feasibility Score: {alt.feasibility_score}")
                
                if alt.risk_level:
                    content_parts.append(f"Risk Level: {alt.risk_level}")
                
                content = "\n".join(content_parts)
                
                knowledge_item = KnowledgeItemCreate(
                    title=f"Alternative Analysis: {alt.option}",
                    content=content,
                    knowledge_type=KnowledgeType.INSIGHT,
                    source_type=SourceType.USER_INPUT,
                    tags=["alternative", "analysis", request.decision_data.decision_type.value, request.project_id],
                    summary=f"Analysis of alternative: {alt.option}",
                    confidence=ConfidenceLevel.MEDIUM,
                    session_id=request.session_id,
                    user_id=request.user_id,
                    project_id=request.project_id,
                    metadata={
                        "alternative_index": i,
                        "parent_decision": request.decision_data.title,
                        "feasibility_score": alt.feasibility_score,
                        "risk_level": alt.risk_level,
                        "pros_count": len(alt.pros),
                        "cons_count": len(alt.cons)
                    }
                )
                
                item = await self.knowledge_service.create_knowledge_item(knowledge_item)
                if item:
                    items.append(item)
        
        return items
    
    async def _create_problem_knowledge_item(self, request: ProblemSolutionIngestionRequest):
        """Create problem knowledge item"""
        problem = request.problem_solution_data.problem
        
        content_parts = [
            f"Problem Category: {problem.category.value}",
            f"Title: {problem.title}"
        ]
        
        if problem.symptoms:
            content_parts.append(f"Symptoms: {'; '.join(problem.symptoms)}")
        
        if problem.error_messages:
            content_parts.append(f"Error Messages: {'; '.join(problem.error_messages[:3])}")
        
        if problem.affected_components:
            content_parts.append(f"Affected Components: {'; '.join(problem.affected_components)}")
        
        if problem.reproduction_steps:
            content_parts.append(f"Reproduction Steps: {'; '.join(problem.reproduction_steps)}")
        
        content = "\n".join(content_parts)
        
        tags = [
            "problem",
            problem.category.value,
            request.project_id
        ]
        
        if problem.severity:
            tags.append(f"severity_{problem.severity}")
        
        knowledge_item = KnowledgeItemCreate(
            title=f"Problem: {problem.title}",
            content=content,
            knowledge_type=KnowledgeType.REFERENCE,
            source_type=SourceType.USER_INPUT,
            tags=tags,
            summary=f"{problem.category.value} problem: {problem.title}",
            confidence=ConfidenceLevel.HIGH,
            session_id=request.session_id,
            user_id=request.user_id,
            project_id=request.project_id,
            metadata={
                "problem_category": problem.category.value,
                "severity": problem.severity,
                "first_occurrence": problem.first_occurrence.isoformat() if problem.first_occurrence else None,
                "affected_components": problem.affected_components,
                "symptoms_count": len(problem.symptoms),
                "error_messages_count": len(problem.error_messages)
            }
        )
        
        return await self.knowledge_service.create_knowledge_item(knowledge_item)
    
    async def _create_solution_knowledge_item(self, request: ProblemSolutionIngestionRequest):
        """Create solution knowledge item"""
        solution = request.problem_solution_data.solution
        problem_title = request.problem_solution_data.problem.title
        
        content_parts = [
            f"Problem: {problem_title}",
            f"Root Cause: {solution.root_cause}"
        ]
        
        if solution.immediate_fix:
            content_parts.append(f"Immediate Fix: {solution.immediate_fix}")
        
        if solution.permanent_solution:
            content_parts.append(f"Permanent Solution: {'; '.join(solution.permanent_solution)}")
        
        if solution.code_changes:
            content_parts.append("Code Changes:")
            for change in solution.code_changes[:5]:  # Limit to first 5
                content_parts.append(f"- {change.get('file', 'Unknown')}: {change.get('change', 'No details')}")
        
        if solution.configuration_changes:
            content_parts.append("Configuration Changes:")
            for change in solution.configuration_changes[:5]:
                content_parts.append(f"- {change.get('config', 'Unknown')}: {change.get('change', 'No details')}")
        
        if solution.prevention_measures:
            content_parts.append(f"Prevention: {'; '.join(solution.prevention_measures)}")
        
        content = "\n".join(content_parts)
        
        tags = [
            "solution",
            request.problem_solution_data.problem.category.value,
            request.project_id,
            "root_cause_analysis"
        ]
        
        knowledge_item = KnowledgeItemCreate(
            title=f"Solution: {problem_title}",
            content=content,
            knowledge_type=KnowledgeType.REFERENCE,
            source_type=SourceType.USER_INPUT,
            tags=tags,
            summary=f"Solution for {problem_title}: {solution.root_cause}",
            confidence=ConfidenceLevel.HIGH,
            session_id=request.session_id,
            user_id=request.user_id,
            project_id=request.project_id,
            metadata={
                "root_cause": solution.root_cause,
                "immediate_fix": solution.immediate_fix,
                "code_changes_count": len(solution.code_changes),
                "config_changes_count": len(solution.configuration_changes),
                "prevention_measures": solution.prevention_measures,
                "related_problem_category": request.problem_solution_data.problem.category.value
            }
        )
        
        return await self.knowledge_service.create_knowledge_item(knowledge_item)
    
    async def _create_verification_knowledge_items(self, request: ProblemSolutionIngestionRequest):
        """Create verification and testing knowledge items"""
        items = []
        verification = request.problem_solution_data.verification
        problem_title = request.problem_solution_data.problem.title
        
        if verification.tests_performed or verification.success_criteria:
            content_parts = [
                f"Problem: {problem_title}",
                "Verification Details:"
            ]
            
            if verification.tests_performed:
                content_parts.append(f"Tests Performed: {'; '.join(verification.tests_performed)}")
            
            if verification.success_criteria:
                content_parts.append(f"Success Criteria: {'; '.join(verification.success_criteria)}")
            
            if verification.monitoring_added:
                content_parts.append(f"Monitoring Added: {'; '.join(verification.monitoring_added)}")
            
            if verification.rollback_plan:
                content_parts.append(f"Rollback Plan: {verification.rollback_plan}")
            
            content = "\n".join(content_parts)
            
            knowledge_item = KnowledgeItemCreate(
                title=f"Verification: {problem_title}",
                content=content,
                knowledge_type=KnowledgeType.REFERENCE,
                source_type=SourceType.USER_INPUT,
                tags=["verification", "testing", request.project_id, request.problem_solution_data.problem.category.value],
                summary=f"Verification plan for {problem_title}",
                confidence=ConfidenceLevel.HIGH,
                session_id=request.session_id,
                user_id=request.user_id,
                project_id=request.project_id,
                metadata={
                    "tests_count": len(verification.tests_performed),
                    "success_criteria_count": len(verification.success_criteria),
                    "monitoring_count": len(verification.monitoring_added),
                    "has_rollback_plan": bool(verification.rollback_plan),
                    "related_problem": problem_title
                }
            )
            
            item = await self.knowledge_service.create_knowledge_item(knowledge_item)
            if item:
                items.append(item)
        
        return items
    
    async def _create_tool_usage_knowledge_item(self, request: ToolUsageIngestionRequest):
        """Create tool usage knowledge item"""
        tool_data = request.tool_usage_data
        
        content_parts = [
            f"Tool: {tool_data.tool_name.value}",
            f"Success: {tool_data.result.success}"
        ]
        
        # Add parameters (sanitized)
        if tool_data.parameters:
            params_summary = []
            for key, value in tool_data.parameters.items():
                if key in ['file_path', 'command', 'pattern']:
                    # Include key parameters
                    value_str = str(value)[:100]  # Limit length
                    params_summary.append(f"{key}: {value_str}")
            if params_summary:
                content_parts.append(f"Parameters: {'; '.join(params_summary)}")
        
        # Add execution details
        if tool_data.result.execution_time_ms:
            content_parts.append(f"Execution Time: {tool_data.result.execution_time_ms}ms")
        
        if tool_data.result.output and len(tool_data.result.output) > 50:
            # Only include output summary for significant outputs
            output_summary = tool_data.result.output[:200] + "..." if len(tool_data.result.output) > 200 else tool_data.result.output
            content_parts.append(f"Output: {output_summary}")
        
        if tool_data.result.error_message:
            content_parts.append(f"Error: {tool_data.result.error_message}")
        
        # Add context
        if tool_data.context.user_intent:
            content_parts.append(f"Intent: {tool_data.context.user_intent}")
        
        if tool_data.context.problem_being_solved:
            content_parts.append(f"Problem: {tool_data.context.problem_being_solved}")
        
        content = "\n".join(content_parts)
        
        tags = [
            "tool_usage",
            tool_data.tool_name.value.lower(),
            request.project_id,
            "success" if tool_data.result.success else "failed"
        ]
        
        # Add file extension tags for file-related tools
        if tool_data.tool_name in [ToolType.READ, ToolType.WRITE, ToolType.EDIT, ToolType.MULTIEDIT]:
            file_path = tool_data.parameters.get('file_path', '')
            if file_path and '.' in file_path:
                ext = file_path.split('.')[-1].lower()
                tags.append(f"ext_{ext}")
        
        knowledge_item = KnowledgeItemCreate(
            title=f"Tool Usage: {tool_data.tool_name.value} - {'Success' if tool_data.result.success else 'Failed'}",
            content=content,
            knowledge_type=KnowledgeType.REFERENCE,
            source_type=SourceType.API,
            tags=tags,
            summary=f"Used {tool_data.tool_name.value} - {tool_data.context.user_intent or 'No intent specified'}",
            confidence=ConfidenceLevel.MEDIUM,
            session_id=request.session_id,
            user_id=request.user_id,
            project_id=request.project_id,
            metadata={
                "tool_name": tool_data.tool_name.value,
                "success": tool_data.result.success,
                "execution_time_ms": tool_data.result.execution_time_ms,
                "has_output": bool(tool_data.result.output),
                "has_error": bool(tool_data.result.error_message),
                "part_of_larger_task": tool_data.context.part_of_larger_task,
                "sequence_number": request.sequence_number,
                "files_affected": tool_data.result.files_affected
            }
        )
        
        return await self.knowledge_service.create_knowledge_item(knowledge_item)
    
    def _prepare_conversation_episode_data(self, request: ConversationIngestionRequest, items: list) -> dict:
        """Prepare episode data for Graphiti from conversation"""
        return {
            "name": f"Claude Conversation - {request.project_id}",
            "content": request.conversation_data.summary or "Claude conversation session",
            "source_description": f"Conversation in project {request.project_id}",
            "reference_time": datetime.now().isoformat(),
            "valid_at": datetime.now().isoformat(),
            "metadata": {
                "session_id": str(request.session_id),
                "project_id": request.project_id,
                "outcome": request.conversation_data.outcome.value,
                "technologies": request.conversation_data.technologies_used,
                "patterns": request.conversation_data.patterns_applied
            }
        }
    
    def _prepare_code_change_episode_data(self, request: CodeChangeIngestionRequest, items: list) -> dict:
        """Prepare episode data for Graphiti from code changes"""
        return {
            "name": f"Code Change - {request.code_change_data.tool_used.value}",
            "content": f"Modified {len(request.code_change_data.files_modified)} files using {request.code_change_data.tool_used.value}",
            "source_description": f"Code modification in project {request.project_id}",
            "reference_time": datetime.now().isoformat(),
            "valid_at": datetime.now().isoformat(),
            "metadata": {
                "session_id": str(request.session_id),
                "project_id": request.project_id,
                "tool_used": request.code_change_data.tool_used.value,
                "files_modified": [fc.file_path for fc in request.code_change_data.files_modified],
                "frameworks": request.code_change_data.technical_context.frameworks_used
            }
        }
    
    def _prepare_decision_episode_data(self, request: DecisionIngestionRequest, items: list) -> dict:
        """Prepare episode data for Graphiti from decisions"""
        return {
            "name": f"Decision: {request.decision_data.title}",
            "content": f"{request.decision_data.context} - Decision: {request.decision_data.final_decision}",
            "source_description": f"Technical decision in project {request.project_id}",
            "reference_time": datetime.now().isoformat(),
            "valid_at": datetime.now().isoformat(),
            "metadata": {
                "project_id": request.project_id,
                "decision_type": request.decision_data.decision_type.value,
                "alternatives_count": len(request.decision_data.alternatives_considered),
                "rationale": request.decision_data.rationale
            }
        }
    
    def _prepare_problem_solution_episode_data(self, request: ProblemSolutionIngestionRequest, items: list) -> dict:
        """Prepare episode data for Graphiti from problem-solution"""
        return {
            "name": f"Problem Solved: {request.problem_solution_data.problem.title}",
            "content": f"Problem: {request.problem_solution_data.problem.title} - Solution: {request.problem_solution_data.solution.root_cause}",
            "source_description": f"Problem resolution in project {request.project_id}",
            "reference_time": datetime.now().isoformat(),
            "valid_at": datetime.now().isoformat(),
            "metadata": {
                "project_id": request.project_id,
                "problem_category": request.problem_solution_data.problem.category.value,
                "resolution_time": request.problem_solution_data.time_to_resolve_minutes,
                "affected_components": request.problem_solution_data.problem.affected_components
            }
        }
    
    def _prepare_tool_usage_episode_data(self, request: ToolUsageIngestionRequest, items: list) -> dict:
        """Prepare episode data for Graphiti from tool usage"""
        return {
            "name": f"Tool Usage: {request.tool_usage_data.tool_name.value}",
            "content": f"Used {request.tool_usage_data.tool_name.value} - Success: {request.tool_usage_data.result.success}",
            "source_description": f"Tool usage in project {request.project_id}",
            "reference_time": datetime.now().isoformat(),
            "valid_at": datetime.now().isoformat(),
            "metadata": {
                "session_id": str(request.session_id),
                "project_id": request.project_id,
                "tool_name": request.tool_usage_data.tool_name.value,
                "success": request.tool_usage_data.result.success,
                "execution_time": request.tool_usage_data.result.execution_time_ms
            }
        }
    
    async def _store_batch_status(self, batch_id: UUID, request: BatchIngestionRequest, response: BatchIngestionResponse):
        """Store batch processing status in PostgreSQL"""
        try:
            query = """
            INSERT INTO batch_ingestion_status (
                batch_id, session_id, project_id, user_id,
                total_items, successful_items, failed_items,
                status, created_at, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """
            
            await self.databases.postgres.execute(
                query,
                batch_id,
                request.session_id,
                request.project_id,
                request.user_id,
                response.total_items,
                response.successful_items,
                response.failed_items,
                "completed",
                datetime.now(),
                json.dumps(response.dict(), default=str)
            )
        except Exception as e:
            logger.error("Failed to store batch status", batch_id=str(batch_id), error=str(e))
    
    async def get_batch_status(self, batch_id: UUID) -> Optional[Dict[str, Any]]:
        """Get batch processing status"""
        try:
            query = """
            SELECT batch_id, session_id, project_id, user_id,
                   total_items, successful_items, failed_items,
                   status, created_at, updated_at, metadata
            FROM batch_ingestion_status
            WHERE batch_id = $1
            """
            
            row = await self.databases.postgres.fetchrow(query, batch_id)
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error("Failed to get batch status", batch_id=str(batch_id), error=str(e))
            return None
    
    async def get_ingestion_stats(self, project_id: Optional[str] = None, days: int = 7) -> Dict[str, Any]:
        """Get ingestion statistics"""
        try:
            base_query = """
            SELECT 
                COUNT(*) as total_batches,
                SUM(total_items) as total_items_processed,
                SUM(successful_items) as total_successful,
                SUM(failed_items) as total_failed,
                AVG(successful_items::float / NULLIF(total_items, 0)) as success_rate
            FROM batch_ingestion_status
            WHERE created_at >= $1
            """
            
            params = [datetime.now() - timedelta(days=days)]
            
            if project_id:
                base_query += " AND project_id = $2"
                params.append(project_id)
            
            row = await self.databases.postgres.fetchrow(base_query, *params)
            
            stats = dict(row) if row else {}
            
            # Add knowledge items stats
            knowledge_query = """
            SELECT knowledge_type, COUNT(*) as count
            FROM knowledge_items
            WHERE created_at >= $1
            """
            
            knowledge_params = [datetime.now() - timedelta(days=days)]
            
            if project_id:
                knowledge_query += " AND metadata->>'project_id' = $2"
                knowledge_params.append(project_id)
            
            knowledge_query += " GROUP BY knowledge_type"
            
            knowledge_rows = await self.databases.postgres.fetch(knowledge_query, *knowledge_params)
            
            stats["knowledge_items_by_type"] = {
                row["knowledge_type"]: row["count"] for row in knowledge_rows
            }
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get ingestion stats", error=str(e))
            return {}
    
    # Background processing methods (simplified for now)
    
    async def process_conversation_background(self, session_id: UUID, result: IngestionResult):
        """Background processing for conversations"""
        logger.info("Background processing conversation", session_id=str(session_id))
        # Add additional processing like relationship building, advanced entity extraction, etc.
    
    async def process_code_change_background(self, session_id: UUID, result: IngestionResult):
        """Background processing for code changes"""
        logger.info("Background processing code change", session_id=str(session_id))
        # Add code analysis, dependency tracking, etc.
    
    async def process_decision_background(self, decision_title: str, result: IngestionResult):
        """Background processing for decisions"""
        logger.info("Background processing decision", decision_title=decision_title)
        # Add decision impact analysis, alternative evaluation, etc.
    
    async def process_problem_solution_background(self, problem_title: str, result: IngestionResult):
        """Background processing for problem-solutions"""
        logger.info("Background processing problem-solution", problem_title=problem_title)
        # Add pattern matching, similar problem detection, etc.
    
    async def process_tool_usage_background(self, session_id: UUID, result: IngestionResult):
        """Background processing for tool usage"""
        logger.info("Background processing tool usage", session_id=str(session_id))
        # Add usage pattern analysis, efficiency metrics, etc.
    
    async def process_batch_background(self, batch_id: UUID, session_id: UUID):
        """Background processing for batch operations"""
        logger.info("Background processing batch", batch_id=str(batch_id), session_id=str(session_id))
        # Add cross-item relationship building, session summary generation, etc.
    
    async def finalize_session_processing(self, session_id: UUID):
        """Finalize processing for a completed Claude session"""
        logger.info("Finalizing session processing", session_id=str(session_id))
        # Add session summary, relationship finalization, quality scoring, etc.