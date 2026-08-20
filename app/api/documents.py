import mimetypes
import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.dependencies.authorization import (
    require_tenant_access,
    require_tenant_admin_access,
)
from app.models.enums import DocumentStatus
from app.models.user import User
from app.schemas.document import (
    DocumentCreate,
    DocumentRead,
    DocumentStatusUpdate,
)
from app.services.document import DocumentService
from app.services.storage import StorageService
from app.schemas.retrieval import (
    RetrievalResponse,
    RetrievalResult,
)
from app.services.retrieval import RetrievalService
from app.rag.qa import (
    RAGQuestionAnsweringService,
)
from app.schemas.rag import (
    RAGAskRequest,
    RAGAskResponse,
    RAGSourceRead,
)


router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)


storage_service = StorageService(
    settings.document_storage_path,
)

document_service = DocumentService(
    storage_service=storage_service,
)

retrieval_service = RetrievalService()

rag_service = RAGQuestionAnsweringService(
    retrieval_service=retrieval_service,
)

@router.post(
    "/{tenant_id}",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_document(
    tenant_id: uuid.UUID,
    payload: DocumentCreate,
    current_user: User = Depends(
        require_tenant_access,
    ),
    db: Session = Depends(get_db),
) -> DocumentRead:
    try:
        document = document_service.create_document(
            db,
            tenant_id=tenant_id,
            uploaded_by=current_user.id,
            filename=payload.filename,
            storage_path=payload.storage_path,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return document


@router.post(
    "/{tenant_id}/upload",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    tenant_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(
        require_tenant_access,
    ),
    db: Session = Depends(get_db),
) -> DocumentRead:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required.",
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file cannot be empty.",
        )

    try:
        document = (
            document_service.create_document_from_upload(
                db,
                tenant_id=tenant_id,
                uploaded_by=current_user.id,
                filename=file.filename,
                content=content,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return document

@router.post(
    "/{tenant_id}/{document_id}/process",
    response_model=DocumentRead,
)
def process_document(
    tenant_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: User = Depends(
        require_tenant_admin_access,
    ),
    db: Session = Depends(get_db),
) -> DocumentRead:
    try:
        return document_service.process_document(
            db,
            document_id=document_id,
            tenant_id=tenant_id,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        if str(exc) == "Document not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

@router.get(
    "/{tenant_id}/retrieve",
    response_model=RetrievalResponse,
)
def retrieve_documents(
    tenant_id: uuid.UUID,
    query: str = Query(
        min_length=1,
    ),
    top_k: int = Query(
        default=5,
        ge=1,
        le=50,
    ),
    current_user: User = Depends(
        require_tenant_access,
    ),
    db: Session = Depends(get_db),
) -> RetrievalResponse:
    try:
        results = retrieval_service.retrieve(
            db,
            tenant_id=tenant_id,
            query=query,
            top_k=top_k,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return RetrievalResponse(
        results=[
            RetrievalResult(
                chunk_id=result.chunk.id,
                document_id=result.chunk.document_id,
                document_filename=(
                    result.chunk.document.filename
                ),
                chunk_index=result.chunk.chunk_index,
                content=result.chunk.content,
                similarity=result.similarity,
            )
            for result in results
        ]
    )

@router.post(
    "/{tenant_id}/ask",
    response_model=RAGAskResponse,
)
def ask_question(
    tenant_id: uuid.UUID,
    payload: RAGAskRequest,
    current_user: User = Depends(
        require_tenant_access,
    ),
    db: Session = Depends(get_db),
) -> RAGAskResponse:
    try:
        result = rag_service.ask(
            db,
            tenant_id=tenant_id,
            question=payload.question,
            top_k=payload.top_k,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return RAGAskResponse(
        question=result.question,
        answer=result.answer,
        abstained=result.abstained,
        sources=[
            RAGSourceRead(
                chunk_id=source.chunk_id,
                document_id=source.document_id,
                document_filename=(
                    source.document_filename
                ),
                chunk_index=source.chunk_index,
                similarity=source.similarity,
            )
            for source in result.sources
        ],
    )

@router.get(
    "/{tenant_id}/{document_id}",
    response_model=DocumentRead,
)
def get_document(
    tenant_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: User = Depends(
        require_tenant_access,
    ),
    db: Session = Depends(get_db),
) -> DocumentRead:
    document = document_service.get_document(
        db,
        document_id,
        tenant_id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    return document


@router.get(
    "/{tenant_id}/{document_id}/download",
)
def download_document(
    tenant_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: User = Depends(
        require_tenant_access,
    ),
    db: Session = Depends(get_db),
) -> FileResponse:
    try:
        result = document_service.get_document_file(
            db,
            document_id=document_id,
            tenant_id=tenant_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    document, path = result

    media_type, _ = mimetypes.guess_type(
        document.filename,
    )

    return FileResponse(
        path=path,
        filename=document.filename,
        media_type=media_type or "application/octet-stream",
    )


@router.get(
    "/{tenant_id}",
    response_model=list[DocumentRead],
)
def list_documents(
    tenant_id: uuid.UUID,
    status_filter: DocumentStatus | None = Query(
        default=None,
        alias="status",
    ),
    current_user: User = Depends(
        require_tenant_access,
    ),
    db: Session = Depends(get_db),
) -> list[DocumentRead]:
    if status_filter is None:
        return document_service.list_tenant_documents(
            db,
            tenant_id,
        )

    return document_service.list_tenant_documents_by_status(
        db,
        tenant_id,
        status_filter,
    )


@router.patch(
    "/{tenant_id}/{document_id}/status",
    response_model=DocumentRead,
)
def update_document_status(
    tenant_id: uuid.UUID,
    document_id: uuid.UUID,
    payload: DocumentStatusUpdate,
    current_user: User = Depends(
        require_tenant_admin_access,
    ),
    db: Session = Depends(get_db),
) -> DocumentRead:
    try:
        return document_service.update_document_status(
            db,
            document_id=document_id,
            tenant_id=tenant_id,
            status=payload.status,
        )
    except ValueError as exc:
        if str(exc) == "Document not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

