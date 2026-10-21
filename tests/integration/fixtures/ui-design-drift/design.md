# Synthetic baseline: Archive Transfer

Status: `Current` for this fixture's baseline only. The approving role is the synthetic product owner defined here; this does not establish a status for any real product.

## User task

A desktop user selects one archive and starts transferring it to a chosen destination. The user needs to know whether the operation is idle, running, failed, or complete and must be able to stop a running transfer safely.

## Approved behavior

- `Start transfer` begins the operation from Idle.
- While Loading, `Cancel transfer` requests cancellation. The result must distinguish completed items from items not transferred; cancellation is not presented as rollback.
- Error shows a concise reason and an available retry action. Retrying must not duplicate already completed items.
- Success reports completion and the destination.
- Idle, Loading, Error, and Success are the baseline visible states. These state names describe the product contract, not implementation widget names.

The HTML mockup is a static representation of these states. Its preview controls only reveal a panel and do not perform transfer behavior.
