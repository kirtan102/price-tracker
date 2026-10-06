"""initial schema"""
from alembic import op
from sqlalchemy import MetaData
revision="0001_initial"; down_revision=None; branch_labels=None; depends_on=None
def upgrade():
    from app.db import Base
    from app import models
    bind=op.get_bind(); Base.metadata.create_all(bind=bind)
def downgrade():
    from app.db import Base
    bind=op.get_bind(); Base.metadata.drop_all(bind=bind)

