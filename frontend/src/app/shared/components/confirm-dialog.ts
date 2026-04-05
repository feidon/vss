import { Component, inject } from '@angular/core';
import { DialogRef, DIALOG_DATA } from '@angular/cdk/dialog';

export interface ConfirmDialogData {
  readonly message: string;
}

@Component({
  selector: 'app-confirm-dialog',
  template: `
    <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div
        class="animate-modal w-full max-w-sm rounded-xl border border-edge bg-panel p-6 shadow-2xl shadow-black/40"
      >
        <p class="mb-6 font-display text-base text-ink">{{ data.message }}</p>
        <div class="flex justify-end gap-3">
          <button
            type="button"
            class="rounded-lg border border-edge px-4 py-2 font-display text-base font-medium text-ink-secondary transition-colors hover:bg-panel-hover hover:text-ink"
            (click)="dialogRef.close(false)"
          >
            Cancel
          </button>
          <button
            type="button"
            class="rounded-lg bg-signal-danger/15 px-4 py-2 font-display text-base font-semibold text-signal-danger ring-1 ring-signal-danger/25 transition-all hover:bg-signal-danger/25 hover:ring-signal-danger/40"
            (click)="dialogRef.close(true)"
          >
            Confirm
          </button>
        </div>
      </div>
    </div>
  `,
})
export class ConfirmDialogComponent {
  readonly dialogRef = inject(DialogRef<boolean>);
  readonly data: ConfirmDialogData = inject(DIALOG_DATA);
}
