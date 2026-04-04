## 1. Remove start time from dialog

- [x] 1.1 Remove `startTime` from `CreateServiceDialogResult` interface in `create-service-dialog.ts`
- [x] 1.2 Remove `startTimeLocal` signal, the datetime-local input field, and its validation error from the dialog template and component
- [x] 1.3 Update `onSubmit` to no longer require or compute `startTime`; close with `{ serviceId: res.id }`
- [x] 1.4 Update `create-service-dialog.spec.ts` to reflect the 2-field form (remove start time validation test expectations)
- [x] 1.5 Run `ng build`, `ng lint`, `ng test` and verify everything passes
