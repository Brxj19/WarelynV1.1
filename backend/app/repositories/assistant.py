from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.models.assistant import AssistantFeedback, AssistantMessage, AssistantSession, FAQChunk, FAQDocument, KnowledgeSourceType

STOP_WORDS = frozenset({
    "how", "do", "i", "a", "an", "the", "is", "are", "what", "why", "when", "where",
    "which", "my", "does", "can", "to", "for", "in", "of", "and", "or", "at", "with",
    "that", "this", "it", "its", "me", "we", "us", "be", "have", "has", "had", "was",
    "were", "will", "would", "could", "should", "may", "might", "not", "no", "get", "got",
})


class AssistantRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_documents(self, tenant_id: int | None) -> list[FAQDocument]:
        return list(
            self.db.scalars(
                select(FAQDocument)
                .where(or_(FAQDocument.tenant_id.is_(None), FAQDocument.tenant_id == tenant_id))
                .order_by(FAQDocument.id.asc())
            )
        )

    def upsert_document(
        self,
        *,
        tenant_id: int | None,
        slug: str,
        title: str,
        source_type: KnowledgeSourceType,
        source_uri: str | None,
        body_text: str,
        metadata_json: dict | None,
        checksum: str,
    ) -> FAQDocument:
        document = self.db.scalar(
            select(FAQDocument).where(FAQDocument.tenant_id == tenant_id, FAQDocument.slug == slug)
        )
        if document is None:
            document = FAQDocument(
                tenant_id=tenant_id,
                slug=slug,
                title=title,
                source_type=source_type,
                source_uri=source_uri,
                body_text=body_text,
                metadata_json=metadata_json,
                checksum=checksum,
            )
            self.db.add(document)
            self.db.flush()
        else:
            document.title = title
            document.source_type = source_type
            document.source_uri = source_uri
            document.body_text = body_text
            document.metadata_json = metadata_json
            document.checksum = checksum
            self.db.flush()
        return document

    def replace_chunks(
        self,
        *,
        document_id: int,
        tenant_id: int | None,
        chunks: list[dict],
    ) -> None:
        self.db.execute(delete(FAQChunk).where(FAQChunk.document_id == document_id))
        for chunk in chunks:
            self.db.add(
                FAQChunk(
                    tenant_id=tenant_id,
                    document_id=document_id,
                    chunk_index=chunk["chunk_index"],
                    content=chunk["content"],
                    searchable_text=chunk["searchable_text"],
                    embedding=chunk.get("embedding"),
                    token_count=chunk.get("token_count"),
                    metadata_json=chunk.get("metadata_json"),
                )
            )
        self.db.flush()

    def count_chunks(self, tenant_id: int | None = None) -> int:
        stmt = select(func.count(FAQChunk.id))
        if tenant_id is None:
            stmt = stmt.where(FAQChunk.tenant_id.is_(None))
        else:
            stmt = stmt.where(or_(FAQChunk.tenant_id.is_(None), FAQChunk.tenant_id == tenant_id))
        return self.db.scalar(stmt) or 0

    def search_keyword_chunks(self, *, tenant_id: int, term: str, limit: int) -> list[FAQChunk]:
        tokens = [
            t.strip("?.,!:;\"'()")
            for t in term.lower().split()
            if len(t.strip("?.,!:;\"'()")) > 2 and t.strip("?.,!:;\"'()") not in STOP_WORDS
        ]
        if not tokens:
            return self.list_recent_chunks(tenant_id=tenant_id, limit=limit)
        conditions = [
            func.lower(FAQChunk.searchable_text).like(f"%{token}%")
            for token in tokens[:6]
        ]
        return list(self.db.scalars(
            select(FAQChunk)
            .where(
                or_(FAQChunk.tenant_id.is_(None), FAQChunk.tenant_id == tenant_id),
                or_(*conditions),
            )
            .order_by(FAQChunk.updated_at.desc(), FAQChunk.id.desc())
            .limit(limit)
        ))

    def list_recent_chunks(self, *, tenant_id: int, limit: int) -> list[FAQChunk]:
        return list(
            self.db.scalars(
                select(FAQChunk)
                .where(or_(FAQChunk.tenant_id.is_(None), FAQChunk.tenant_id == tenant_id))
                .order_by(FAQChunk.updated_at.desc(), FAQChunk.id.desc())
                .limit(limit)
            )
        )

    def create_session(self, *, tenant_id: int, user_id: int, title: str) -> AssistantSession:
        session = AssistantSession(tenant_id=tenant_id, user_id=user_id, title=title)
        self.db.add(session)
        self.db.flush()
        return session

    def get_session(self, *, tenant_id: int, session_id: int) -> AssistantSession | None:
        return self.db.scalar(
            select(AssistantSession).where(AssistantSession.id == session_id, AssistantSession.tenant_id == tenant_id)
        )

    def list_sessions_for_user(self, *, tenant_id: int, user_id: int) -> list[AssistantSession]:
        return list(
            self.db.scalars(
                select(AssistantSession)
                .where(AssistantSession.tenant_id == tenant_id, AssistantSession.user_id == user_id)
                .order_by(AssistantSession.updated_at.desc(), AssistantSession.id.desc())
            )
        )

    def create_message(
        self,
        *,
        tenant_id: int,
        session_id: int,
        user_id: int | None,
        role: str,
        content: str,
        confidence_score: float | None = None,
        citations_json: list[dict] | None = None,
        suggested_actions_json: list[dict] | None = None,
        usage_json: dict | None = None,
        metadata_json: dict | None = None,
    ) -> AssistantMessage:
        message = AssistantMessage(
            tenant_id=tenant_id,
            session_id=session_id,
            user_id=user_id,
            role=role,
            content=content,
            confidence_score=confidence_score,
            citations_json=citations_json,
            suggested_actions_json=suggested_actions_json,
            usage_json=usage_json,
            metadata_json=metadata_json,
        )
        self.db.add(message)
        self.db.flush()
        return message

    def list_messages(self, *, tenant_id: int, session_id: int) -> list[AssistantMessage]:
        return list(
            self.db.scalars(
                select(AssistantMessage)
                .where(AssistantMessage.tenant_id == tenant_id, AssistantMessage.session_id == session_id)
                .order_by(AssistantMessage.created_at.asc(), AssistantMessage.id.asc())
            )
        )

    def get_message(self, *, tenant_id: int, message_id: int) -> AssistantMessage | None:
        return self.db.scalar(
            select(AssistantMessage).where(AssistantMessage.id == message_id, AssistantMessage.tenant_id == tenant_id)
        )

    def upsert_feedback(
        self,
        *,
        tenant_id: int,
        message_id: int,
        user_id: int,
        value: str,
        note: str | None,
    ) -> AssistantFeedback:
        feedback = self.db.scalar(
            select(AssistantFeedback).where(
                AssistantFeedback.tenant_id == tenant_id,
                AssistantFeedback.message_id == message_id,
                AssistantFeedback.user_id == user_id,
            )
        )
        if feedback is None:
            feedback = AssistantFeedback(
                tenant_id=tenant_id,
                message_id=message_id,
                user_id=user_id,
                value=value,
                note=note,
            )
            self.db.add(feedback)
            self.db.flush()
        else:
            feedback.value = value
            feedback.note = note
            self.db.flush()
        return feedback
