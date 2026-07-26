from sqlalchemy.orm import Session

from app.models.document import Document


class DocumentRepository:

    @staticmethod
    def create(
        db: Session,
        title: str,
        source_type: str,
        file_name: str | None = None,
        source_url: str | None = None,
        content: str | None = None,
    ) -> Document:
        document = Document(
            title=title,
            source_type=source_type,
            file_name=file_name,
            source_url=source_url,
            content=content,
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        return document

    @staticmethod
    def get_all(db: Session) -> list[Document]:
        return (
            db.query(Document)
            .order_by(Document.created_at.desc())
            .all()
        )

    @staticmethod
    def get_by_id(db: Session, document_id: str) -> Document | None:
        return (
            db.query(Document)
            .filter(Document.id == document_id)
            .first()
        )

    @staticmethod
    def get_by_title(db: Session, title: str) -> Document | None:
        return (
            db.query(Document)
            .filter(Document.title == title)
            .first()
        )

    @staticmethod
    def get_by_source_url(db: Session, source_url: str) -> Document | None:
        return (
            db.query(Document)
            .filter(Document.source_url == source_url)
            .first()
        )

    @staticmethod
    def delete(db: Session, document: Document) -> None:
        db.delete(document)
        db.commit()
