"""FastAPI Server Entrypoint and E2E Integration Application.

Coordinates REST APIs and WebSocket endpoints with relational databases,
Document/Chat/Search/Embedding agents, and vector engines.
"""

from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import logging
import os
from typing import Any, Dict, List, Optional
import uuid

# FastAPI imports
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Nexus Core imports
from backend.api.sqlite_mock import DBStorage
from backend.providers.qdrant_vector import QdrantVectorProvider
from backend.interfaces.vector import VectorRegistry, CollectionInfo, VectorRecord
from backend.interfaces.model import ModelRegistry, InferenceRequest
from backend.providers.openai_provider import OpenAIProvider, ProviderConfiguration
from backend.providers.ollama_provider import OllamaProvider, OllamaConfiguration
from backend.agents.workspace import (
    Workspace,
    WorkspaceMember,
    Project,
    KnowledgeSpace,
    ConversationReference,
    WorkspaceProvider,
    WorkspaceRegistry,
    WorkspaceAgent,
    WorkspaceRole
)
from backend.agents.document import DocumentAgent, Document, DocumentStatus
from backend.agents.embedding import EmbeddingAgent
from backend.agents.search import SearchAgent
from backend.agents.chat import ChatAgent, ChatRequest, ConversationMessage
from backend.runtime.task import Task
from backend.runtime.event import EventBus


# =====================================================================
# Database backed Workspace Provider
# =====================================================================

class DBWorkspaceProvider(WorkspaceProvider):
    """Adapter bridging relational DBStorage queries with the WorkspaceProvider interface."""

    def __init__(self, db: DBStorage) -> None:
        self.db = db

    def create_workspace(self, workspace: Workspace) -> Workspace:
        self.db.create_workspace(
            workspace_id=workspace.workspace_id,
            name=workspace.name,
            owner_id=workspace.owner_id
        )
        return workspace

    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        row = self.db.list_workspaces(user_id="") # Select all is handled
        # Fetching directly from DB table
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM workspaces WHERE workspace_id = ?", (workspace_id,))
        r = cursor.fetchone()
        conn.close()
        if not r:
            return None
        return Workspace(
            workspace_id=r["workspace_id"],
            name=r["name"],
            description="",
            owner_id=r["owner_id"],
            organization_id="",
            created_at=datetime.fromisoformat(r["created_at"]) if r["created_at"] else datetime.utcnow(),
            updated_at=datetime.utcnow(),
            status=r["status"]
        )

    def update_workspace(self, workspace: Workspace) -> Workspace:
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE workspaces SET name = ?, status = ? WHERE workspace_id = ?",
            (workspace.name, workspace.status, workspace.workspace_id)
        )
        conn.commit()
        conn.close()
        return workspace

    def delete_workspace(self, workspace_id: str) -> bool:
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM workspaces WHERE workspace_id = ?", (workspace_id,))
        conn.commit()
        conn.close()
        return True

    def add_member(self, member: WorkspaceMember) -> WorkspaceMember:
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO members (workspace_id, user_id, role, status) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(workspace_id, user_id) DO UPDATE SET role = ?, status = ?",
            (member.workspace_id, member.user_id, member.role.value, member.status, member.role.value, member.status)
        )
        conn.commit()
        conn.close()
        return member

    def get_members(self, workspace_id: str) -> List[WorkspaceMember]:
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM members WHERE workspace_id = ?", (workspace_id,))
        rows = cursor.fetchall()
        conn.close()
        members = []
        for r in rows:
            members.append(WorkspaceMember(
                member_id=f"{workspace_id}-{r['user_id']}",
                workspace_id=workspace_id,
                user_id=r["user_id"],
                role=WorkspaceRole(r["role"]),
                joined_at=datetime.utcnow(),
                status=r["status"]
            ))
        return members

    def remove_member(self, workspace_id: str, user_id: str) -> bool:
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM members WHERE workspace_id = ? AND user_id = ?", (workspace_id, user_id))
        conn.commit()
        conn.close()
        return True

    def create_project(self, project: Project) -> Project:
        return project

    def list_projects(self, workspace_id: str) -> List[Project]:
        return []

    def create_knowledge_space(self, space: KnowledgeSpace) -> KnowledgeSpace:
        return space

    def get_knowledge_spaces(self, workspace_id: str) -> List[KnowledgeSpace]:
        return [KnowledgeSpace(
            knowledge_space_id=f"ks-{workspace_id}",
            workspace_id=workspace_id,
            name="Default Knowledge Space",
            description="Automatic",
            indexing_status="indexed"
        )]

    def create_conversation_reference(self, ref: ConversationReference) -> ConversationReference:
        self.db.create_conversation(ref.conversation_id, ref.workspace_id, ref.title)
        return ref

    def get_conversations(self, workspace_id: str) -> List[ConversationReference]:
        rows = self.db.list_conversations(workspace_id)
        return [
            ConversationReference(
                conversation_id=r["conversation_id"],
                workspace_id=workspace_id,
                title=r["title"],
                created_at=datetime.fromisoformat(r["created_at"]) if r["created_at"] else datetime.utcnow()
            )
            for r in rows
        ]

    def health_check(self) -> bool:
        return True


# =====================================================================
# Lifespans & Dependency Injections
# =====================================================================

db_storage = DBStorage()
workspace_provider = DBWorkspaceProvider(db_storage)

# Initialize and Register agents
workspace_registry = WorkspaceRegistry()
workspace_registry.register_provider("db_provider", workspace_provider)

vector_provider = QdrantVectorProvider(mock=True)
VectorRegistry().register_provider("qdrant", vector_provider)

# Ensure collection exists
VectorRegistry().get_provider("qdrant").create_collection(CollectionInfo(
    collection_id="default_wiki",
    name="Wiki Collection",
    dimensions=384,
    similarity_metric="cosine"
))

# Configure default embedding providers in registry
from backend.agents.embedding import EmbeddingRegistry, MockEmbeddingProvider
EmbeddingRegistry().register_provider("mock_embedding", MockEmbeddingProvider())

# Configure Default Ollama / OpenAI Models in Registry
model_provider = OllamaProvider(config=OllamaConfiguration(host="mock-host", metadata={"mock": True}))
model_provider.initialize()
ModelRegistry().register_provider("ollama", model_provider)

# Configure search providers registry
from backend.agents.search import SearchRegistry, SearchProvider, SearchRequest as AgentSearchRequest, SearchResult as AgentSearchResult
from backend.interfaces.vector import SearchRequest as VectorSearchRequest

class VectorSearchProvider(SearchProvider):
    def __init__(self, vector_registry: VectorRegistry):
        self.vector_registry = vector_registry

    def search(self, request: AgentSearchRequest) -> List[AgentSearchResult]:
        from backend.agents.embedding import EmbeddingRegistry
        embed_provider = EmbeddingRegistry().get_provider("mock_embedding")
        embeddings = embed_provider.generate_embeddings([request.query], "mock-embed-small")[0]

        col_id = f"col_{request.workspace_id}"
        vec_provider = self.vector_registry.get_provider("qdrant")
        col_exists = any(c.collection_id == col_id for c in vec_provider.list_collections())
        if not col_exists:
            return []

        results = vec_provider.search(VectorSearchRequest(
            embedding=embeddings,
            collection=col_id,
            top_k=request.top_k
        ))

        agent_results = []
        for r in results:
            agent_results.append(AgentSearchResult(
                result_id=r.vector_id,
                document_id=r.metadata.get("document_id", "doc"),
                chunk_id=r.metadata.get("chunk_id", "chunk"),
                score=r.score,
                snippet=r.metadata.get("text", ""),
                source="knowledge_base",
                metadata=r.metadata
            ))
        return agent_results

    def search_keyword(self, request: AgentSearchRequest) -> List[AgentSearchResult]:
        return self.search(request)

    def search_hybrid(self, request: AgentSearchRequest) -> List[AgentSearchResult]:
        return self.search(request)

    def suggest(self, query: str, limit: int = 5) -> List[str]:
        return []

    def health_check(self) -> bool:
        return True

SearchRegistry().register_provider("vector_search", VectorSearchProvider(VectorRegistry()))

workspace_agent = WorkspaceAgent()
workspace_agent.initialize()

document_agent = DocumentAgent()
document_agent.initialize()

embedding_agent = EmbeddingAgent()
embedding_agent.initialize()

search_agent = SearchAgent()
search_agent.initialize()

chat_agent = ChatAgent()
chat_agent.initialize()

# Seed default workspace if none exist
try:
    conn = db_storage._get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM workspaces WHERE workspace_id = 'default-ws'")
    if cursor.fetchone()[0] == 0:
        db_storage.create_workspace("default-ws", "Default Workspace", "admin")
    conn.commit()
    conn.close()
except Exception:
    pass


# =====================================================================
# API Request / Response schemas
# =====================================================================

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str


class LoginRequest(BaseModel):
    username: str
    password: str


class WorkspaceCreateRequest(BaseModel):
    name: str


# =====================================================================
# FastAPI Routing
# =====================================================================

app = FastAPI(title="Nexus AI REST & WebSocket Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/auth/register")
def register_user(req: RegisterRequest):
    user = db_storage.get_user(req.username)
    if user:
        raise HTTPException(status_code=400, detail="User username already exists.")
    # Standard password hash simulation
    password_hash = f"hashed_{req.password}"
    db_storage.create_user(req.username, password_hash, req.email)
    return {"status": "success", "message": "User registered successfully."}


@app.post("/api/auth/login")
def login_user(req: LoginRequest):
    user = db_storage.get_user(req.username)
    if not user or user["password_hash"] != f"hashed_{req.password}":
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    # Return mock token containing user ID
    token = f"token_for_{req.username}_{uuid.uuid4()}"
    return {"token": token, "username": req.username, "role": user["role"]}


@app.post("/api/workspaces")
def create_workspace(req: WorkspaceCreateRequest, user_id: str = "admin"):
    task = Task(
        description="Create workspace",
        metadata={
            "action": "create_workspace",
            "workspace_id": f"ws-{str(uuid.uuid4())[:8]}",
            "name": req.name,
            "owner_id": user_id
        }
    )
    res = workspace_agent.execute(task)
    return {"status": "success", "workspace": res}


@app.get("/api/workspaces")
def list_workspaces(user_id: str = "admin"):
    rows = db_storage.list_workspaces(user_id)
    return {"workspaces": rows}


@app.post("/api/documents/upload")
async def upload_document(workspace_id: str, file: UploadFile = File(...)):
    contents = await file.read()
    text = contents.decode("utf-8", errors="ignore")

    doc_id = f"doc-{str(uuid.uuid4())[:8]}"
    checksum = str(hash(text))

    # Relational entry
    db_storage.create_document(doc_id, workspace_id, file.filename, checksum)

    # background ingestion parsing
    # Chunking & Embeddings generation using EmbeddingAgent
    task_embed = Task(
        description="Index document content",
        metadata={
            "action": "embed",
            "workspace_id": workspace_id,
            "document_id": doc_id,
            "text": text,
            "filename": file.filename,
            "checksum": checksum,
            "collection": "default_wiki"
        }
    )
    embedding_agent.execute(task_embed)
    db_storage.update_document_status(doc_id, "indexed")

    return {"status": "success", "document_id": doc_id}


@app.get("/api/documents")
def list_documents(workspace_id: str):
    rows = db_storage.list_documents(workspace_id)
    return {"documents": rows}


@app.get("/api/health")
def health_dashboard():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": True,
            "vector_store": True,
            "ollama_provider": True
        }
    }


# =====================================================================
# Streaming WebSocket Chat
# =====================================================================

@app.websocket("/api/chat/ws")
async def websocket_chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)

            action = payload.get("action")
            if action == "send_message":
                conv_id = payload.get("conversation_id")
                ws_id = payload.get("workspace_id")
                message = payload.get("message")
                user_id = payload.get("user_id", "admin")

                if not conv_id:
                    # Create new E2E conversation automatically
                    conv_id = f"conv-{str(uuid.uuid4())[:8]}"
                    db_storage.create_conversation(conv_id, ws_id, f"Conversation: {message[:15]}")

                try:
                    chat_agent.registry.get_conversation(conv_id)
                except Exception:
                    from backend.agents.chat import Conversation
                    chat_agent.registry._conversations[conv_id] = Conversation(
                        conversation_id=conv_id,
                        workspace_id=ws_id,
                        title=f"Conversation: {message[:15]}",
                        participants=[user_id],
                        messages=[],
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )

                # Relational message log (User)
                db_storage.create_message(str(uuid.uuid4()), conv_id, "user", message)

                # Process Streaming Chat Agent response
                task = Task(
                    description="Streaming message response",
                    metadata={
                        "action": "stream",
                        "conversation_id": conv_id,
                        "workspace_id": ws_id,
                        "user_id": user_id,
                        "message": message
                    }
                )
                stream_adapter = chat_agent.execute(task)

                # Stream chunks back over websocket
                assistant_full_reply = ""
                for token in stream_adapter.stream_tokens():
                    assistant_full_reply += token
                    await websocket.send_json({
                        "conversation_id": conv_id,
                        "token": token,
                        "citations": [
                            {"source": c.source, "document_id": c.document_id}
                            for c in stream_adapter.get_citations()
                        ]
                    })

                # Relational message log (Assistant)
                db_storage.create_message(str(uuid.uuid4()), conv_id, "assistant", assistant_full_reply)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"error": str(e)})
        await websocket.close()
