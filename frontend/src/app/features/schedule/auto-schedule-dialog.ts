import { Component, inject, signal, computed } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { DialogRef } from '@angular/cdk/dialog';
import { ScheduleService } from '../../core/services/schedule.service';
import { GenerateScheduleResponse } from '../../shared/models';
import { ErrorAlertComponent } from '../../shared/components/error-alert';
import { extractErrorMessage } from '../../shared/utils/error-utils';
import { localDatetimeToEpoch } from '../../shared/utils/time-utils';

export interface AutoScheduleDialogResult {
  readonly response: GenerateScheduleResponse;
}

@Component({
  selector: 'app-auto-schedule-dialog',
  imports: [FormsModule, ErrorAlertComponent],
  template: `
    <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div
        class="animate-modal w-full max-w-md rounded-xl bg-panel border border-edge p-6 shadow-2xl shadow-black/40"
      >
        @if (result()) {
          <h3 class="mb-5 font-display text-xl font-bold text-signal-clear">Schedule Generated</h3>
          <div class="mb-6 space-y-3">
            <div class="flex justify-between rounded-lg bg-panel-raised px-4 py-3 ring-1 ring-edge">
              <span class="font-display text-sm text-ink-muted">Services created</span>
              <span class="font-display text-base font-semibold text-ink">
                {{ result()!.services_created }}
              </span>
            </div>
            <div class="flex justify-between rounded-lg bg-panel-raised px-4 py-3 ring-1 ring-edge">
              <span class="font-display text-sm text-ink-muted">Vehicles used</span>
              <span class="font-display text-base font-semibold text-ink">
                {{ result()!.vehicles_used.length }}
              </span>
            </div>
            <div class="flex justify-between rounded-lg bg-panel-raised px-4 py-3 ring-1 ring-edge">
              <span class="font-display text-sm text-ink-muted">Cycle time</span>
              <span class="font-display text-base font-semibold text-ink">
                {{ formatSeconds(result()!.cycle_time_seconds) }}
              </span>
            </div>
          </div>
          <div class="flex justify-end">
            <button
              type="button"
              class="rounded-lg bg-signal-clear/15 px-5 py-2.5 font-display text-base font-semibold text-signal-clear ring-1 ring-signal-clear/25 transition-all hover:bg-signal-clear/25 hover:ring-signal-clear/40 hover:shadow-[0_0_16px_var(--color-glow-green)]"
              (click)="onDone()"
            >
              Done
            </button>
          </div>
        } @else {
          <h3 class="mb-5 font-display text-xl font-bold text-ink">Auto Schedule</h3>

          <div
            class="mb-5 flex items-start gap-3 rounded-lg border border-signal-caution/30 bg-signal-caution/5 px-4 py-3"
          >
            <svg
              class="mt-0.5 h-5 w-5 shrink-0 text-signal-caution"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fill-rule="evenodd"
                d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.168 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z"
                clip-rule="evenodd"
              />
            </svg>
            <p class="font-display text-sm text-signal-caution">
              This will <strong>delete all existing services</strong> and generate a new schedule.
              This action cannot be undone.
            </p>
          </div>

          @if (errorMessage()) {
            <app-error-alert [message]="errorMessage()!" (dismiss)="errorMessage.set(null)" />
          }

          <form (ngSubmit)="onGenerate()">
            <div class="mb-4">
              <label
                class="mb-1.5 block font-display text-sm font-semibold uppercase tracking-wider text-ink-muted"
                for="dlg-interval"
              >
                Interval (seconds)
              </label>
              <input
                id="dlg-interval"
                type="number"
                class="h-10 w-full rounded-lg px-3 font-display text-base"
                [(ngModel)]="intervalSeconds"
                name="intervalSeconds"
                min="1"
                required
                [disabled]="generating()"
              />
            </div>

            <div class="mb-4 grid grid-cols-2 gap-4">
              <div>
                <label
                  class="mb-1.5 block font-display text-sm font-semibold uppercase tracking-wider text-ink-muted"
                  for="dlg-start"
                >
                  Start Time
                </label>
                <input
                  id="dlg-start"
                  type="datetime-local"
                  class="h-10 w-full rounded-lg px-3 font-display text-base"
                  [(ngModel)]="startTime"
                  name="startTime"
                  required
                  [disabled]="generating()"
                />
              </div>
              <div>
                <label
                  class="mb-1.5 block font-display text-sm font-semibold uppercase tracking-wider text-ink-muted"
                  for="dlg-end"
                >
                  End Time
                </label>
                <input
                  id="dlg-end"
                  type="datetime-local"
                  class="h-10 w-full rounded-lg px-3 font-display text-base"
                  [(ngModel)]="endTime"
                  name="endTime"
                  required
                  [disabled]="generating()"
                />
              </div>
            </div>

            <div class="mb-6">
              <label
                class="mb-1.5 block font-display text-sm font-semibold uppercase tracking-wider text-ink-muted"
                for="dlg-dwell"
              >
                Dwell Time (seconds)
              </label>
              <input
                id="dlg-dwell"
                type="number"
                class="h-10 w-full rounded-lg px-3 font-display text-base"
                [(ngModel)]="dwellTimeSeconds"
                name="dwellTimeSeconds"
                min="1"
                required
                [disabled]="generating()"
              />
            </div>

            <div class="flex justify-end gap-3">
              <button
                type="button"
                class="rounded-lg border border-edge px-4 py-2.5 font-display text-base font-medium text-ink-secondary transition-colors hover:bg-panel-hover hover:text-ink disabled:opacity-30"
                (click)="onCancel()"
                [disabled]="generating()"
              >
                Cancel
              </button>
              <button
                type="submit"
                class="rounded-lg bg-signal-caution/15 px-5 py-2.5 font-display text-base font-semibold text-signal-caution ring-1 ring-signal-caution/25 transition-all hover:bg-signal-caution/25 hover:ring-signal-caution/40 disabled:opacity-30"
                [disabled]="generating() || !formValid()"
              >
                @if (generating()) {
                  <span class="flex items-center gap-2">
                    <span
                      class="inline-block h-4 w-4 animate-spin rounded-full border-2 border-signal-caution/30 border-t-signal-caution"
                    ></span>
                    Generating...
                  </span>
                } @else {
                  Generate
                }
              </button>
            </div>
          </form>
        }
      </div>
    </div>
  `,
})
export class AutoScheduleDialogComponent {
  private readonly dialogRef = inject(DialogRef<AutoScheduleDialogResult>);
  private readonly scheduleService = inject(ScheduleService);

  readonly intervalSeconds = signal<number | null>(null);
  readonly startTime = signal('');
  readonly endTime = signal('');
  readonly dwellTimeSeconds = signal<number | null>(null);

  readonly generating = signal(false);
  readonly errorMessage = signal<string | null>(null);
  readonly result = signal<GenerateScheduleResponse | null>(null);

  readonly formValid = computed(() => {
    const interval = this.intervalSeconds();
    const start = this.startTime();
    const end = this.endTime();
    const dwell = this.dwellTimeSeconds();
    return (
      interval !== null &&
      interval > 0 &&
      start !== '' &&
      end !== '' &&
      dwell !== null &&
      dwell > 0 &&
      end > start
    );
  });

  onGenerate(): void {
    if (!this.formValid()) return;

    this.generating.set(true);
    this.errorMessage.set(null);

    this.scheduleService
      .generate({
        interval_seconds: this.intervalSeconds()!,
        start_time: localDatetimeToEpoch(this.startTime()),
        end_time: localDatetimeToEpoch(this.endTime()),
        dwell_time_seconds: this.dwellTimeSeconds()!,
      })
      .subscribe({
        next: (response) => {
          this.result.set(response);
          this.generating.set(false);
        },
        error: (err: HttpErrorResponse) => {
          this.errorMessage.set(extractErrorMessage(err, 'Failed to generate schedule.'));
          this.generating.set(false);
        },
      });
  }

  onCancel(): void {
    this.dialogRef.close();
  }

  onDone(): void {
    this.dialogRef.close({ response: this.result()! });
  }

  formatSeconds(totalSeconds: number): string {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return seconds > 0 ? `${minutes}m ${seconds}s` : `${minutes}m`;
  }
}
