## 1. Fix stops queue refresh

- [x] 1.1 In `route-editor.ts`, move `deriveInitialState()` call from `ngOnInit()` into an `effect()` in the constructor that watches `this.service()`
- [x] 1.2 Remove the now-unnecessary `ngOnInit()` method and `OnInit` import
- [x] 1.3 Update or add tests in `route-editor.spec.ts` verifying stops reset when service input changes

## 2. Fix block name resolution in timetable and conflict alert

- [x] 2.1 In `route-editor.ts`, extend `nodeName()` to also search `graph.edges` for block names
- [x] 2.2 In `conflict-alert.ts`, extend the `nodeNameMap` computed signal to also iterate over `this.graph().edges` and map edge IDs to names
- [x] 2.3 Update tests in `conflict-alert.spec.ts` to use real mockGraph instead of graphWithBlockNodes() workaround

## 3. Verify

- [x] 3.1 Run `ng test` and confirm all tests pass
- [x] 3.2 Run `ng lint` and confirm no lint errors
