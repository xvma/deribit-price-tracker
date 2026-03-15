from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create price_records table
    op.create_table(
        'price_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticker', sa.String(length=20), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('idx_ticker_timestamp', 'price_records', ['ticker', 'timestamp'])
    op.create_index('idx_ticker', 'price_records', ['ticker'])
    op.create_index(op.f('ix_price_records_id'), 'price_records', ['id'], unique=False)

def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_price_records_id'), table_name='price_records')
    op.drop_index('idx_ticker', table_name='price_records')
    op.drop_index('idx_ticker_timestamp', table_name='price_records')

    # Drop table
    op.drop_table('price_records')