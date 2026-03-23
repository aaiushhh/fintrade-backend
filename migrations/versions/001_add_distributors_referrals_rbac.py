"""add distributors referrals and rbac columns

Revision ID: 001_add_dist_rbac
Revises: (initial)
Create Date: 2026-03-16
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '001_add_dist_rbac'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Create distributors table FIRST (other FKs reference it) ─────
    # op.create_table(
    #     'distributors',
    #     sa.Column('id', sa.Integer(), primary_key=True, index=True),
    #     sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
    #     sa.Column('region', sa.String(255), nullable=False),
    #     sa.Column('referral_code', sa.String(50), nullable=False, unique=True, index=True),
    #     sa.Column('discount_percentage', sa.Float(), server_default='0.0'),
    #     sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    # )

    # ── Create student_referrals table ───────────────────────────────
    # op.create_table(
    #     'student_referrals',
    #     sa.Column('id', sa.Integer(), primary_key=True, index=True),
    #     sa.Column('student_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
    #     sa.Column('distributor_id', sa.Integer(), sa.ForeignKey('distributors.id', ondelete='CASCADE'), nullable=False),
    #     sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False),
    #     sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    # )

    # ── Add created_by to users ──────────────────────────────────────
    op.add_column('users', sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True))

    # ── Add columns to offers ────────────────────────────────────────
    op.add_column('offers', sa.Column('created_by_admin', sa.Integer(), sa.ForeignKey('users.id'), nullable=True))
    op.add_column('offers', sa.Column('distributor_id', sa.Integer(), sa.ForeignKey('distributors.id', ondelete='SET NULL'), nullable=True))

    # ── Add columns to course_enrollments ────────────────────────────
    op.add_column('course_enrollments', sa.Column('discount_applied', sa.Float(), server_default='0.0', nullable=True))
    op.add_column('course_enrollments', sa.Column('price_paid', sa.Float(), nullable=True))
    op.add_column('course_enrollments', sa.Column('distributor_id', sa.Integer(), sa.ForeignKey('distributors.id', ondelete='SET NULL'), nullable=True))


def downgrade() -> None:
    op.drop_column('course_enrollments', 'distributor_id')
    op.drop_column('course_enrollments', 'price_paid')
    op.drop_column('course_enrollments', 'discount_applied')
    op.drop_column('offers', 'distributor_id')
    op.drop_column('offers', 'created_by_admin')
    op.drop_column('users', 'created_by')
    op.drop_table('student_referrals')
    op.drop_table('distributors')
