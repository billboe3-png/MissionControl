"""add_hyperv_unique_constraints

Revision ID: h7h8h9i1j2k3
Revises: a1b2c3d4e5f8
Create Date: 2026-09-18

Adds the composite unique constraints that the Hyper-V plugin sync
requires for its ON CONFLICT (host_id, <entity_id>) upserts:
- hyperv_vms (host_id, vm_id)
- hyperv_networks (host_id, switch_id)
- hyperv_volumes (host_id, disk_id)
- hyperv_checkpoints (host_id, checkpoint_id)
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "h7h8h9i1j2k3"
down_revision: str | None = "a1b2c3d4e5f8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_hyperv_vms_host_vm_id", "hyperv_vms", ["host_id", "vm_id"]
    )
    op.create_unique_constraint(
        "uq_hyperv_networks_host_switch_id", "hyperv_networks", ["host_id", "switch_id"]
    )
    op.create_unique_constraint(
        "uq_hyperv_volumes_host_disk_id", "hyperv_volumes", ["host_id", "disk_id"]
    )
    op.create_unique_constraint(
        "uq_hyperv_checkpoints_host_ckpt_id", "hyperv_checkpoints", ["host_id", "checkpoint_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_hyperv_checkpoints_host_ckpt_id", "hyperv_checkpoints")
    op.drop_constraint("uq_hyperv_volumes_host_disk_id", "hyperv_volumes")
    op.drop_constraint("uq_hyperv_networks_host_switch_id", "hyperv_networks")
    op.drop_constraint("uq_hyperv_vms_host_vm_id", "hyperv_vms")