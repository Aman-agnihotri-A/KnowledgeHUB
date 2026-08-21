import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.authorization import (
    require_conversation_user_access,
)
from app.models.user import User
from app.rag.qa import RAGQuestionAnsweringService
from app.schemas.rag import (
    RAGAskRequest,
    RAGAskResponse,
    RAGSourceRead,
)


router = APIRouter(
    prefix="/rag",
    tags=["rag"],
)


rag_service = RAGQuestionAnsweringService()


@router.post(
    "/{tenant_id}/ask",
    response_model=RAGAskResponse,
)
def ask_question(
    tenant_id: uuid.UUID,
    payload: RAGAskRequest,
    current_user: User = Depends(
        require_conversation_user_access,
    ),
    db: Session = Depends(get_db),
) -> RAGAskResponse:
    try:
        result = rag_service.ask(
            db,
            tenant_id=tenant_id,
            user_id=current_user.id,
            question=payload.question,
            top_k=payload.top_k,
            conversation_id=payload.conversation_id,
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
                document_filename=source.document_filename,
                chunk_index=source.chunk_index,
                similarity=source.similarity,
            )
            for source in result.sources
        ],
        conversation_id=result.conversation_id,
    )