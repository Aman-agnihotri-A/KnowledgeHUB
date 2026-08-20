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
from app.schemas.conversation import (
    ConversationCreate,
    ConversationMessageRead,
    ConversationRead,
    ConversationSummary,
)
from app.services.conversation import (
    ConversationService,
)


router = APIRouter(
    prefix="/conversations",
    tags=["conversations"],
)


conversation_service = ConversationService()


@router.post(
    "/{tenant_id}",
    response_model=ConversationSummary,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    tenant_id: uuid.UUID,
    payload: ConversationCreate,
    current_user: User = Depends(
        require_conversation_user_access,
    ),
    db: Session = Depends(get_db),
) -> ConversationSummary:
    try:
        conversation = (
            conversation_service.create_conversation(
                db,
                tenant_id=tenant_id,
                user_id=current_user.id,
                title=payload.title,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return ConversationSummary.model_validate(
        conversation,
    )


@router.get(
    "/{tenant_id}",
    response_model=list[ConversationSummary],
)
def list_conversations(
    tenant_id: uuid.UUID,
    current_user: User = Depends(
        require_conversation_user_access,
    ),
    db: Session = Depends(get_db),
) -> list[ConversationSummary]:
    conversations = (
        conversation_service.list_user_conversations(
            db,
            tenant_id=tenant_id,
            user_id=current_user.id,
        )
    )

    return [
        ConversationSummary.model_validate(
            conversation,
        )
        for conversation in conversations
    ]


@router.get(
    "/{tenant_id}/{conversation_id}",
    response_model=ConversationRead,
)
def get_conversation(
    tenant_id: uuid.UUID,
    conversation_id: uuid.UUID,
    current_user: User = Depends(
        require_conversation_user_access,
    ),
    db: Session = Depends(get_db),
) -> ConversationRead:
    conversation = conversation_service.get_conversation(
        db,
        conversation_id=conversation_id,
        tenant_id=tenant_id,
        user_id=current_user.id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    messages = conversation_service.list_messages(
        db,
        conversation_id=conversation_id,
        tenant_id=tenant_id,
        user_id=current_user.id,
    )

    return ConversationRead(
        id=conversation.id,
        tenant_id=conversation.tenant_id,
        user_id=conversation.user_id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[
            ConversationMessageRead.model_validate(
                message,
            )
            for message in messages
        ],
    )