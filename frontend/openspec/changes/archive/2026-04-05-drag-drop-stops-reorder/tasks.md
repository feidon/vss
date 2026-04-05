## 1. CDK Drag-Drop Integration

- [x] 1.1 Import `CdkDragDrop`, `CdkDrag`, `CdkDropList`, and `moveItemInArray` in `RouteEditorComponent`
- [x] 1.2 Add `cdkDropList` directive to the stops list container and `cdkDrag` to each stop row
- [x] 1.3 Implement `onDrop(event: CdkDragDrop<StopEntry[]>)` handler that creates a reordered array via immutable update and sets the `stops` signal

## 2. Drag Handle & Visual Feedback

- [x] 2.1 Add a grip/drag-handle icon to the left side of each stop row with `cdkDragHandle`
- [x] 2.2 Style the CDK drag placeholder (`.cdk-drag-placeholder`) to show a dashed-border gap at the drop target
- [x] 2.3 Style the CDK drag preview (`.cdk-drag-preview`) to match the stop row appearance

## 3. Verification & Testing

- [x] 3.1 Verify track map order numbers update reactively after reorder (existing `queuedStopIds` computed signal)
- [x] 3.2 Verify add, remove, and dwell-time edit still work after reordering
- [x] 3.3 Verify dropping at the same position is a no-op (no unnecessary signal update)
