import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.document import DocumentCreate, DocumentRead
from app.services.document import DocumentService

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)

document_service = DocumentService()


@router.post(
    "/{tenant_id}",
    response_model=DocumentRead,
    status_code=201,
)
def create_document(
    tenant_id: uuid.UUID,
    payload: DocumentCreate,
    uploaded_by: uuid.UUID,
    db: Session = Depends(get_db),
) -> DocumentRead:
    try:
        document = document_service.create_document(
            db,
            tenant_id=tenant_id,
            uploaded_by=uploaded_by,
            filename=payload.filename,
            storage_path=payload.storage_path,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return document


@router.get(
    "/{tenant_id}/{document_id}",
    response_model=DocumentRead,
)
def get_document(
    tenant_id: uuid.UUID,
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> DocumentRead:
    document = document_service.get_document(
        db,
        document_id,
        tenant_id,
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    return document


@router.get(
    "/{tenant_id}",
    response_model=list[DocumentRead],
)
def list_documents(
    tenant_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> list[DocumentRead]:
    return document_service.list_tenant_documents(
        db,
        tenant_id,
    )