"""initial schema + full-text search trigger"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)
TS = sa.text("now()")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("google_sub", sa.Text, unique=True, nullable=True),
        sa.Column("email", sa.Text, nullable=False, unique=True),
        sa.Column("display_name", sa.Text, nullable=True),
        sa.Column("avatar_url", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=TS),
    )

    op.create_table(
        "imports",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("source", sa.Text, nullable=False),
        sa.Column("filename", sa.Text, nullable=True),
        sa.Column("total_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("processed_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.Text, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=TS),
    )

    op.create_table(
        "articles",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("import_id", UUID, sa.ForeignKey("imports.id"), nullable=True),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("title", sa.Text, nullable=True),
        sa.Column("byline", sa.Text, nullable=True),
        sa.Column("lead_image_url", sa.Text, nullable=True),
        sa.Column("excerpt", sa.Text, nullable=True),
        sa.Column("word_count", sa.Integer, nullable=True),
        sa.Column("reading_minutes", sa.Integer, nullable=True),
        sa.Column("saved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_archived", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_favorite", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("extraction_status", sa.Text, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=TS),
        sa.UniqueConstraint("user_id", "url", name="uq_articles_user_url"),
    )
    op.create_index("ix_articles_user_id", "articles", ["user_id"])

    op.create_table(
        "article_content",
        sa.Column(
            "article_id", UUID,
            sa.ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True,
        ),
        sa.Column("content_html", sa.Text, nullable=True),
        sa.Column("content_text", sa.Text, nullable=True),
        sa.Column("search_vector", postgresql.TSVECTOR, nullable=True),
        sa.Column("extracted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "tags",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.UniqueConstraint("user_id", "name", name="uq_tags_user_name"),
    )

    op.create_table(
        "article_tags",
        sa.Column("article_id", UUID, sa.ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", UUID, sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "highlights",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("article_id", UUID, sa.ForeignKey("articles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quote", sa.Text, nullable=False),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("position", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=TS),
    )
    op.create_index("ix_highlights_article_id", "highlights", ["article_id"])

    op.execute(
        """
        CREATE OR REPLACE FUNCTION article_content_tsv_update()
        RETURNS trigger AS $$
        DECLARE
            v_title text;
        BEGIN
            SELECT title INTO v_title FROM articles WHERE id = NEW.article_id;
            NEW.search_vector :=
                setweight(to_tsvector('english', coalesce(v_title, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(NEW.content_text, '')), 'B');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_article_content_tsv
        BEFORE INSERT OR UPDATE OF content_text ON article_content
        FOR EACH ROW EXECUTE FUNCTION article_content_tsv_update();
        """
    )
    op.create_index(
        "idx_article_search",
        "article_content",
        ["search_vector"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("idx_article_search", table_name="article_content")
    op.execute("DROP TRIGGER IF EXISTS trg_article_content_tsv ON article_content;")
    op.execute("DROP FUNCTION IF EXISTS article_content_tsv_update();")
    op.drop_index("ix_highlights_article_id", table_name="highlights")
    op.drop_table("highlights")
    op.drop_table("article_tags")
    op.drop_table("tags")
    op.drop_table("article_content")
    op.drop_index("ix_articles_user_id", table_name="articles")
    op.drop_table("articles")
    op.drop_table("imports")
    op.drop_table("users")
