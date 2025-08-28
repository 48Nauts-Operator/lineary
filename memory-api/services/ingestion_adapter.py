# ABOUTME: Adapter service for ingesting Claude sessions into existing BETTY schema
# ABOUTME: Bridges new ingestion models with existing database structure

import asyncio
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
import structlog
from sqlalchemy import text

from models.ingestion import (
    ConversationIngestionRequest,
    CodeChangeIngestionRequest,
    DecisionIngestionRequest,
    ProblemSolutionIngestionRequest,
    ToolUsageIngestionRequest,
    IngestionResult
)
from core.dependencies import DatabaseDependencies

logger = structlog.get_logger(__name__)

class IngestionAdapter:
    """Adapter to convert ingestion requests to existing database schema"""
    
    def __init__(self, databases: DatabaseDependencies):
        self.databases = databases
    
    async def ingest_conversation(self, request: ConversationIngestionRequest) -> IngestionResult:
        """Ingest conversation into existing knowledge_items table"""
        start_time = datetime.now()
        
        try:
            # Ensure project and user exist
            project_uuid = await self._ensure_project_exists(request.project_id)
            user_uuid = await self._ensure_user_exists(request.user_id)
            
            # Create knowledge item from conversation
            knowledge_id = uuid4()
            # Make session_id optional since sessions table may not have the entry
            session_uuid = None  # Set to None to avoid foreign key constraint
            
            # Build content from messages
            content_parts = []
            for msg in request.conversation_data.messages:
                role_label = msg.role.value.upper()
                content_parts.append(f"{role_label}: {msg.content}")
            
            content = "\n\n".join(content_parts)
            
            # Create content hash
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # Extract technologies and patterns
            technologies = request.conversation_data.technologies_used
            patterns = request.conversation_data.patterns_applied
            
            # Create metadata
            metadata = {
                "source": "claude_ingestion",
                "ingestion_type": "conversation", 
                "claude_version": request.claude_version,
                "environment": request.environment,
                "duration_minutes": request.duration_minutes,
                "outcome": request.conversation_data.outcome.value,
                "message_count": len(request.conversation_data.messages),
                "key_decisions": request.conversation_data.key_decisions,
                "lessons_learned": request.conversation_data.lessons_learned,
                "summary": request.conversation_data.summary
            }
            
            # Insert into knowledge_items table
            query = text("""
                INSERT INTO knowledge_items (
                    id, project_id, user_id, session_id,
                    title, content, content_hash, knowledge_type,
                    technologies, patterns, metadata,
                    problem_description, solution_description, outcome_description,
                    lessons_learned
                ) VALUES (
                    :id, :project_id, :user_id, :session_id,
                    :title, :content, :content_hash, :knowledge_type,
                    :technologies, :patterns, :metadata,
                    :problem_description, :solution_description, :outcome_description,
                    :lessons_learned
                )
            """)
            
            await self.databases.postgres.execute(query, {
                "id": knowledge_id,
                "project_id": project_uuid,
                "user_id": user_uuid,
                "session_id": session_uuid,
                "title": f"Claude Conversation - {request.project_id} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "content": content,
                "content_hash": content_hash,
                "knowledge_type": "conversation",
                "technologies": json.dumps(technologies),
                "patterns": json.dumps(patterns), 
                "metadata": json.dumps(metadata),
                "problem_description": self._extract_problem_description(request),
                "solution_description": self._extract_solution_description(request),
                "outcome_description": request.conversation_data.summary,
                "lessons_learned": "; ".join(request.conversation_data.lessons_learned) if request.conversation_data.lessons_learned else None
            })
            
            # Log the ingestion
            await self._log_ingestion(
                session_id=str(session_uuid),
                project_id=request.project_id,
                user_id=request.user_id,
                ingestion_type="conversation",
                knowledge_item_id=str(knowledge_id),
                success=True,
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                metadata=metadata
            )
            
            logger.info(
                "Conversation ingested successfully",
                session_id=str(session_uuid),
                knowledge_id=str(knowledge_id),
                project_id=request.project_id
            )
            
            return IngestionResult(
                success=True,
                item_id=knowledge_id,
                knowledge_items_created=1,
                entities_extracted=len(technologies) + len(patterns),
                relationships_created=0,
                embeddings_generated=0,
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000
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
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
    
    async def ingest_code_change(self, request: CodeChangeIngestionRequest) -> IngestionResult:
        """Ingest code change into existing knowledge_items table"""
        start_time = datetime.now()
        
        try:
            project_uuid = await self._ensure_project_exists(request.project_id)
            user_uuid = await self._ensure_user_exists(request.user_id)
            
            knowledge_id = uuid4()
            
            # Build content from code changes
            content_parts = [
                f"Tool Used: {request.code_change_data.tool_used.value}",
                f"Files Modified: {len(request.code_change_data.files_modified)}"
            ]
            
            for file_change in request.code_change_data.files_modified:
                file_info = f"- {file_change.file_path} ({file_change.operation.value})"
                if file_change.change_intent:
                    file_info += f": {file_change.change_intent}"
                content_parts.append(file_info)
            
            content = "\n".join(content_parts)
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            technologies = request.code_change_data.technical_context.frameworks_used
            patterns = request.code_change_data.technical_context.patterns_applied
            
            metadata = {
                "source": "claude_ingestion",
                "ingestion_type": "code_change",
                "tool_used": request.code_change_data.tool_used.value,
                "files_count": len(request.code_change_data.files_modified),
                "technical_context": request.code_change_data.technical_context.dict(),
                "success_indicators": request.code_change_data.success_indicators,
                "error_messages": request.code_change_data.error_messages
            }
            
            query = text("""
                INSERT INTO knowledge_items (
                    id, project_id, user_id, session_id,
                    title, content, content_hash, knowledge_type,
                    technologies, patterns, metadata
                ) VALUES (
                    :id, :project_id, :user_id, :session_id,
                    :title, :content, :content_hash, :knowledge_type,
                    :technologies, :patterns, :metadata
                )
            """)
            
            await self.databases.postgres.execute(query, {
                "id": knowledge_id,
                "project_id": project_uuid,
                "user_id": user_uuid,
                "session_id": None,  # Avoid FK constraint
                "title": f"Code Change - {request.code_change_data.tool_used.value} - {request.project_id}",
                "content": content,
                "content_hash": content_hash,
                "knowledge_type": "code",
                "technologies": json.dumps(technologies),
                "patterns": json.dumps(patterns),
                "metadata": json.dumps(metadata)
            })
            
            await self._log_ingestion(
                session_id=str(request.session_id),
                project_id=request.project_id,
                user_id=request.user_id,
                ingestion_type="code_change", 
                knowledge_item_id=str(knowledge_id),
                success=True,
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                metadata=metadata
            )
            
            return IngestionResult(
                success=True,
                item_id=knowledge_id,
                knowledge_items_created=1,
                entities_extracted=len(technologies) + len(patterns),
                relationships_created=0,
                embeddings_generated=0,
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            
        except Exception as e:
            return IngestionResult(
                success=False,
                error_message=str(e),
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
    
    async def ingest_decision(self, request: DecisionIngestionRequest) -> IngestionResult:
        """Ingest decision into existing knowledge_items table"""
        start_time = datetime.now()
        
        try:
            project_uuid = await self._ensure_project_exists(request.project_id)
            user_uuid = await self._ensure_user_exists(request.user_id)
            
            knowledge_id = uuid4()
            
            # Build content from decision
            content_parts = [
                f"Decision Type: {request.decision_data.decision_type.value}",
                f"Context: {request.decision_data.context}",
                f"Final Decision: {request.decision_data.final_decision}"
            ]
            
            if request.decision_data.alternatives_considered:
                content_parts.append("\nAlternatives Considered:")
                for alt in request.decision_data.alternatives_considered:
                    alt_text = f"- {alt.option}"
                    if alt.pros:
                        alt_text += f" (Pros: {', '.join(alt.pros[:3])})"
                    if alt.cons:
                        alt_text += f" (Cons: {', '.join(alt.cons[:3])})"
                    content_parts.append(alt_text)
            
            content = "\n".join(content_parts)
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            metadata = {
                "source": "claude_ingestion",
                "ingestion_type": "decision",
                "decision_type": request.decision_data.decision_type.value,
                "alternatives_count": len(request.decision_data.alternatives_considered),
                "rationale": request.decision_data.rationale,
                "implementation_plan": request.decision_data.implementation_plan,
                "success_criteria": request.decision_data.success_criteria
            }
            
            query = text("""
                INSERT INTO knowledge_items (
                    id, project_id, user_id, session_id,
                    title, content, content_hash, knowledge_type,
                    metadata, problem_description, solution_description
                ) VALUES (
                    :id, :project_id, :user_id, :session_id,
                    :title, :content, :content_hash, :knowledge_type,
                    :metadata, :problem_description, :solution_description
                )
            """)
            
            await self.databases.postgres.execute(query, {
                "id": knowledge_id,
                "project_id": project_uuid,
                "user_id": user_uuid,
                "session_id": None,  # Avoid FK constraint
                "title": request.decision_data.title,
                "content": content,
                "content_hash": content_hash,
                "knowledge_type": "decision",
                "metadata": json.dumps(metadata),
                "problem_description": request.decision_data.context,
                "solution_description": request.decision_data.final_decision
            })
            
            await self._log_ingestion(
                session_id=str(request.session_id) if request.session_id else None,
                project_id=request.project_id,
                user_id=request.user_id,
                ingestion_type="decision",
                knowledge_item_id=str(knowledge_id),
                success=True,
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                metadata=metadata
            )
            
            return IngestionResult(
                success=True,
                item_id=knowledge_id,
                knowledge_items_created=1,
                entities_extracted=0,
                relationships_created=0,
                embeddings_generated=0,
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            
        except Exception as e:
            return IngestionResult(
                success=False,
                error_message=str(e),
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
    
    async def _ensure_project_exists(self, project_id: str) -> UUID:
        """Ensure project exists and return its UUID"""
        # First check if it exists by name
        query = text("SELECT id FROM projects WHERE name = :name")
        result = await self.databases.postgres.execute(query, {"name": project_id})
        row = result.fetchone()
        
        if row:
            return row[0]
        
        # Create new project
        project_uuid = uuid4()
        query = text("""
            INSERT INTO projects (id, name, description, metadata)
            VALUES (:id, :name, :description, :metadata)
            ON CONFLICT (name) DO UPDATE SET updated_at = NOW()
            RETURNING id
        """)
        
        result = await self.databases.postgres.execute(query, {
            "id": project_uuid,
            "name": project_id,
            "description": f"Auto-created project for {project_id}",
            "metadata": json.dumps({"auto_created": True, "source": "claude_ingestion"})
        })
        
        return project_uuid
    
    async def _ensure_user_exists(self, user_id: str) -> UUID:
        """Ensure user exists and return its UUID"""
        # First check if it exists by username
        query = text("SELECT id FROM users WHERE username = :username")
        result = await self.databases.postgres.execute(query, {"username": user_id})
        row = result.fetchone()
        
        if row:
            return row[0]
        
        # Create new user
        user_uuid = uuid4()
        query = text("""
            INSERT INTO users (id, username, display_name, email, metadata)
            VALUES (:id, :username, :display_name, :email, :metadata)
            ON CONFLICT (username) DO UPDATE SET updated_at = NOW()
            RETURNING id
        """)
        
        result = await self.databases.postgres.execute(query, {
            "id": user_uuid,
            "username": user_id,
            "display_name": user_id,
            "email": f"{user_id}@claude.ai",
            "metadata": json.dumps({"auto_created": True, "source": "claude_ingestion"})
        })
        
        return user_uuid
    
    async def _log_ingestion(
        self,
        session_id: Optional[str],
        project_id: str,
        user_id: str,
        ingestion_type: str,
        knowledge_item_id: str,
        success: bool,
        processing_time_ms: float,
        metadata: Dict[str, Any]
    ):
        """Log ingestion operation if the table exists"""
        try:
            query = text("""
                INSERT INTO knowledge_ingestion_logs (
                    session_id, project_id, user_id, ingestion_type,
                    knowledge_item_id, success, processing_time_ms, metadata
                ) VALUES (
                    :session_id, :project_id, :user_id, :ingestion_type,
                    :knowledge_item_id, :success, :processing_time_ms, :metadata
                )
            """)
            
            await self.databases.postgres.execute(query, {
                "session_id": UUID(session_id) if session_id else None,
                "project_id": project_id,
                "user_id": user_id,
                "ingestion_type": ingestion_type,
                "knowledge_item_id": UUID(knowledge_item_id),
                "success": success,
                "processing_time_ms": processing_time_ms,
                "metadata": json.dumps(metadata)
            })
        except Exception as e:
            # Log but don't fail if ingestion logging fails
            logger.warning("Failed to log ingestion operation", error=str(e))
    
    def _extract_problem_description(self, request: ConversationIngestionRequest) -> Optional[str]:
        """Extract problem description from conversation"""
        for message in request.conversation_data.messages:
            if message.role.value == "user" and message.context and message.context.problem_category:
                return message.content[:500]  # First user message with problem context
        return None
    
    def _extract_solution_description(self, request: ConversationIngestionRequest) -> Optional[str]:
        """Extract solution description from conversation"""
        if request.conversation_data.summary:
            return request.conversation_data.summary
        
        # Find first assistant message
        for message in request.conversation_data.messages:
            if message.role.value == "assistant":
                return message.content[:500]
        
        return None
    
    async def ingest_problem_solution(self, request: ProblemSolutionIngestionRequest) -> IngestionResult:
        """Ingest problem-solution pair into existing knowledge_items table"""
        start_time = datetime.now()
        
        try:
            project_uuid = await self._ensure_project_exists(request.project_id)
            user_uuid = await self._ensure_user_exists(request.user_id)
            
            knowledge_id = uuid4()
            
            # Build content from problem-solution
            problem = request.problem_solution_data.problem
            solution = request.problem_solution_data.solution
            
            content_parts = [
                f"Problem: {problem.title}",
                f"Category: {problem.category.value}",
                f"Root Cause: {solution.root_cause}",
                f"Solution: {'; '.join(solution.permanent_solution)}"
            ]
            
            if problem.symptoms:
                content_parts.append(f"Symptoms: {'; '.join(problem.symptoms)}")
            
            content = "\n".join(content_parts)
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            metadata = {
                "source": "claude_ingestion",
                "ingestion_type": "problem_solution",
                "problem_category": problem.category.value,
                "severity": problem.severity,
                "time_to_resolve_minutes": request.problem_solution_data.time_to_resolve_minutes
            }
            
            query = text("""
                INSERT INTO knowledge_items (
                    id, project_id, user_id, session_id,
                    title, content, content_hash, knowledge_type,
                    metadata, problem_description, solution_description,
                    lessons_learned
                ) VALUES (
                    :id, :project_id, :user_id, :session_id,
                    :title, :content, :content_hash, :knowledge_type,
                    :metadata, :problem_description, :solution_description,
                    :lessons_learned
                )
            """)
            
            await self.databases.postgres.execute(query, {
                "id": knowledge_id,
                "project_id": project_uuid,
                "user_id": user_uuid,
                "session_id": None,  # Avoid FK constraint
                "title": f"Problem-Solution: {problem.title}",
                "content": content,
                "content_hash": content_hash,
                "knowledge_type": "problem_solution",
                "metadata": json.dumps(metadata),
                "problem_description": problem.title,
                "solution_description": solution.root_cause,
                "lessons_learned": '; '.join(solution.prevention_measures) if solution.prevention_measures else None
            })
            
            await self._log_ingestion(
                session_id=str(request.session_id) if request.session_id else None,
                project_id=request.project_id,
                user_id=request.user_id,
                ingestion_type="problem_solution",
                knowledge_item_id=str(knowledge_id),
                success=True,
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                metadata=metadata
            )
            
            return IngestionResult(
                success=True,
                item_id=knowledge_id,
                knowledge_items_created=1,
                entities_extracted=0,
                relationships_created=0,
                embeddings_generated=0,
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            
        except Exception as e:
            return IngestionResult(
                success=False,
                error_message=str(e),
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
    
    async def ingest_tool_usage(self, request: ToolUsageIngestionRequest) -> IngestionResult:
        """Ingest tool usage into existing knowledge_items table"""
        start_time = datetime.now()
        
        try:
            project_uuid = await self._ensure_project_exists(request.project_id)
            user_uuid = await self._ensure_user_exists(request.user_id)
            
            knowledge_id = uuid4()
            
            # Build content from tool usage
            tool_data = request.tool_usage_data
            
            content_parts = [
                f"Tool: {tool_data.tool_name.value}",
                f"Success: {tool_data.result.success}"
            ]
            
            if tool_data.context.user_intent:
                content_parts.append(f"Intent: {tool_data.context.user_intent}")
            
            if tool_data.result.output and len(tool_data.result.output) > 50:
                output_summary = tool_data.result.output[:200]
                content_parts.append(f"Output: {output_summary}")
            
            content = "\n".join(content_parts)
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            metadata = {
                "source": "claude_ingestion",
                "ingestion_type": "tool_usage",
                "tool_name": tool_data.tool_name.value,
                "success": tool_data.result.success,
                "execution_time_ms": tool_data.result.execution_time_ms,
                "parameters": tool_data.parameters
            }
            
            query = text("""
                INSERT INTO knowledge_items (
                    id, project_id, user_id, session_id,
                    title, content, content_hash, knowledge_type,
                    metadata
                ) VALUES (
                    :id, :project_id, :user_id, :session_id,
                    :title, :content, :content_hash, :knowledge_type,
                    :metadata
                )
            """)
            
            await self.databases.postgres.execute(query, {
                "id": knowledge_id,
                "project_id": project_uuid,
                "user_id": user_uuid,
                "session_id": None,  # Avoid FK constraint
                "title": f"Tool Usage: {tool_data.tool_name.value}",
                "content": content,
                "content_hash": content_hash,
                "knowledge_type": "tool_usage",
                "metadata": json.dumps(metadata)
            })
            
            await self._log_ingestion(
                session_id=str(request.session_id),
                project_id=request.project_id,
                user_id=request.user_id,
                ingestion_type="tool_usage",
                knowledge_item_id=str(knowledge_id),
                success=True,
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                metadata=metadata
            )
            
            return IngestionResult(
                success=True,
                item_id=knowledge_id,
                knowledge_items_created=1,
                entities_extracted=0,
                relationships_created=0,
                embeddings_generated=0,
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            
        except Exception as e:
            return IngestionResult(
                success=False,
                error_message=str(e),
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )