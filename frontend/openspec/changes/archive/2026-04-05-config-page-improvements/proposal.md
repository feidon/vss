## Why

The config page has two usability issues: (1) the "-" placeholder for ungrouped blocks is not horizontally centered in the group column, creating visual misalignment, and (2) there is no way to view the list of vehicles in the system — users must navigate elsewhere to see vehicle information.

## What Changes

- Fix horizontal centering of the "-" text in the block table's group column so it aligns with the grouped badges above/below it.
- Add a new "Vehicles" section to the config page that lists all vehicles sorted by ID, displaying each vehicle's name.

## Non-goals

- No vehicle editing or CRUD operations — this is a read-only vehicle list.
- No changes to block editing functionality or other config page behavior.
- No changes to the track map overview section.

## Capabilities

### New Capabilities

- `vehicle-list-config`: Read-only vehicle list section on the config page, fetching from VehicleService and displaying vehicles sorted by ID.

### Modified Capabilities

_(none — block group centering is a CSS fix, not a spec-level behavior change)_

## Impact

- **ConfigComponent** (`src/app/features/config/config.ts`): Will import and render a new vehicle list component alongside BlockConfigComponent.
- **BlockConfigComponent** (`src/app/features/config/block-config.ts`): Minor template fix for group column centering.
- **VehicleService** (`src/app/core/services/vehicle.service.ts`): Already exists, will be consumed by the new vehicle list component.
- No API changes required — `GET /api/vehicles` already exists.
