from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.config import settings
from app.core.logging import get_logger
from app.database.session import get_db
from app.models.user import User
from app.repositories.user import UserRepository
from app.utils.security import verify_password, create_access_token
from app.agents.manager import AgentManager
from app.rag.service import RAGService
from app.tools.manager import ToolManager
from app.services.chat_service import ChatService
from app.services.document_service import DocumentService
from app.services.agent_service import AgentService
from app.workflows.n8n.webhook_handler import router as n8n_router
from app.core.exceptions import AgentPlatformException, AgentNotFoundError
import aiofiles
from pathlib import Path

logger = get_logger("api.app")
app = FastAPI(
    title=settings.app_name,
    description="Professional modular AI agent platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()


class ChatRequest(BaseModel):
    message: str
    agent_name: str
    conversation_id: int | None = None


class ChatResponse(BaseModel):
    conversation_id: int
    message_id: int
    content: str
    sources: list = []
    tokens_used: int | None = None
    latency_ms: int | None = None
    model: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AgentInfo(BaseModel):
    name: str
    display_name: str
    description: str
    model: str
    temperature: float
    tools: list
    is_active: bool
    vector_collection: str


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    token = credentials.credentials
    payload = create_access_token
    from app.utils.security import decode_access_token
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    user_repo = UserRepository(db)
    user = user_repo.get_by_email(payload.get("sub", ""))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    return user


from fastapi.security import OAuth2PasswordRequestForm

@app.post(f"{settings.app_api_prefix}/auth/login", response_model=TokenResponse, summary="Login to get access token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    user = user_repo.get_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.email})
    return TokenResponse(access_token=access_token)


@app.get(f"{settings.app_api_prefix}/health", summary="Health check")
def health():
    agent_manager = AgentManager()
    agents = agent_manager.list_agents()
    return {
        "status": "ok",
        "version": "1.0.0",
        "agents_loaded": len(agents),
        "collections": [],
    }


@app.get(f"{settings.app_api_prefix}/agents", response_model=list[AgentInfo], summary="List all available agents")
def list_agents(current_user: User = Depends(get_current_user)):
    agent_manager = AgentManager()
    return agent_manager.list_agents()


@app.post(f"{settings.app_api_prefix}/agents/reload", summary="Reload all agents from YAML files")
def reload_agents(current_user: User = Depends(get_current_user)):
    agent_manager = AgentManager()
    names = agent_manager.reload()
    return {"reloaded": names}


@app.post(f"{settings.app_api_prefix}/chat", response_model=ChatResponse, summary="Send a message to an agent")
async def chat(request: ChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    agent_manager = AgentManager()
    rag_service = RAGService()
    tool_manager = ToolManager()
    chat_service = ChatService(db, agent_manager, rag_service, tool_manager)
    from app.agents.base import AgentContext
    context = AgentContext(conversation_id=request.conversation_id, user_id=current_user.id)
    result = await chat_service.chat(current_user, request)
    return ChatResponse(**result)


@app.post(f"{settings.app_api_prefix}/documents/upload", summary="Upload a document for ingestion")
async def upload_document(
    file: UploadFile = File(...),
    collection_name: str = "default",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    upload_dir = Path("./data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file.filename
    try:
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            await f.write(content)
        document_service = DocumentService(db, RAGService())
        result = await document_service.ingest_file(current_user.id, str(file_path), collection_name, chunk_size, chunk_overlap)
        return result
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get(f"{settings.app_api_prefix}/documents", summary="List ingested documents")
def list_documents(
    collection_name: str | None = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document_service = DocumentService(db, RAGService())
    docs = document_service.get_documents(collection_name, skip, limit)
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "collection_name": d.collection_name,
            "status": d.status.value,
            "chunk_count": d.chunk_count,
            "created_at": d.created_at.isoformat(),
        }
        for d in docs
    ]


logger.info(f"API application created at {settings.app_api_prefix}")

app.include_router(n8n_router, prefix="/workflows", tags=["Workflows"])
