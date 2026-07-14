"""Add encrypted credential columns

Adds password_encrypted, private_key_encrypted, passphrase_encrypted,
and key_version columns to credential_profiles. Migrates any existing
plaintext passwords to encrypted values.

Revision ID: o5p6q7r8s9t0
Revises: i9j0k1l2m3n4
Create Date: 2026-07-13
"""

import os

import sqlalchemy as sa

from alembic import op

revision = "o5p6q7r8s9t0"
down_revision = "i9j0k1l2m3n4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add encrypted columns
    op.add_column(
        "credential_profiles",
        sa.Column("password_encrypted", sa.Text(), nullable=True),
    )
    op.add_column(
        "credential_profiles",
        sa.Column("private_key_encrypted", sa.Text(), nullable=True),
    )
    op.add_column(
        "credential_profiles",
        sa.Column("passphrase_encrypted", sa.Text(), nullable=True),
    )
    op.add_column(
        "credential_profiles",
        sa.Column(
            "key_version",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )

    # Migrate existing plaintext data to encrypted columns
    # Only if MISSIONCONTROL_SECRET_KEY is available
    secret_key = os.environ.get("MISSIONCONTROL_SECRET_KEY")
    if secret_key:
        from cryptography.fernet import Fernet

        fernet = Fernet(secret_key.encode())

        # Get all credential profiles with plaintext data
        conn = op.get_bind()
        result = conn.execute(
            sa.text(
                "SELECT id, password, ssh_key FROM credential_profiles "
                "WHERE password IS NOT NULL OR ssh_key IS NOT NULL"
            )
        )

        for row in result:
            cred_id, password, ssh_key = row

            # Encrypt password if present
            if password:
                encrypted_password = fernet.encrypt(
                    password.encode("utf-8")
                ).decode("utf-8")
                conn.execute(
                    sa.text(
                        "UPDATE credential_profiles "
                        "SET password_encrypted = :encrypted "
                        "WHERE id = :id"
                    ),
                    {"encrypted": encrypted_password, "id": cred_id},
                )

            # Encrypt SSH key if present (stored as private_key_encrypted)
            if ssh_key:
                encrypted_key = fernet.encrypt(
                    ssh_key.encode("utf-8")
                ).decode("utf-8")
                conn.execute(
                    sa.text(
                        "UPDATE credential_profiles "
                        "SET private_key_encrypted = :encrypted "
                        "WHERE id = :id"
                    ),
                    {"encrypted": encrypted_key, "id": cred_id},
                )


def downgrade() -> None:
    op.drop_column("credential_profiles", "key_version")
    op.drop_column("credential_profiles", "passphrase_encrypted")
    op.drop_column("credential_profiles", "private_key_encrypted")
    op.drop_column("credential_profiles", "password_encrypted")
