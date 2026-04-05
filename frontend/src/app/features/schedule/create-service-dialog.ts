import { Component, inject, OnInit, signal } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { DialogRef } from '@angular/cdk/dialog';
import { VehicleService } from '../../core/services/vehicle.service';
import { ServiceService } from '../../core/services/service.service';
import { Vehicle } from '../../shared/models';
import { ErrorAlertComponent } from '../../shared/components/error-alert';
import { extractErrorMessage } from '../../shared/utils/error-utils';

export interface CreateServiceDialogResult {
  readonly serviceId: number;
}

@Component({
  selector: 'app-create-service-dialog',
  imports: [FormsModule, ErrorAlertComponent],
  template: `
    <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div
        class="animate-modal w-full max-w-md rounded-xl bg-panel border border-edge p-6 shadow-2xl shadow-black/40"
      >
        <h3 class="mb-5 font-display text-lg font-bold text-ink">Create Service</h3>

        @if (loadError()) {
          <app-error-alert [message]="loadError()!" (dismiss)="loadError.set(null)" />
        }

        @if (createError()) {
          <app-error-alert [message]="createError()!" (dismiss)="createError.set(null)" />
        }

        <form (ngSubmit)="onSubmit()">
          <div class="mb-4">
            <label
              class="mb-1.5 block font-display text-xs font-semibold uppercase tracking-wider text-ink-muted"
              for="dlg-name"
            >
              Name
            </label>
            <input
              id="dlg-name"
              class="h-10 w-full rounded-lg px-3 font-display text-sm"
              [(ngModel)]="name"
              name="name"
              placeholder="e.g. S101"
              required
            />
            @if (submitted() && !name().trim()) {
              <p class="mt-1.5 font-display text-xs text-signal-danger">Name is required</p>
            }
          </div>

          <div class="mb-6">
            <label
              class="mb-1.5 block font-display text-xs font-semibold uppercase tracking-wider text-ink-muted"
              for="dlg-vehicle"
            >
              Vehicle
            </label>
            <select
              id="dlg-vehicle"
              class="h-10 w-full rounded-lg px-3 font-display text-sm"
              [(ngModel)]="vehicleId"
              name="vehicleId"
              [disabled]="loading()"
              required
            >
              <option value="" disabled>Select vehicle</option>
              @for (v of vehicles(); track v.id) {
                <option [value]="v.id">{{ v.name }}</option>
              }
            </select>
            @if (submitted() && !vehicleId()) {
              <p class="mt-1.5 font-display text-xs text-signal-danger">Vehicle is required</p>
            }
          </div>

          <div class="flex justify-end gap-3">
            <button
              type="button"
              class="rounded-lg border border-edge px-4 py-2.5 font-display text-sm font-medium text-ink-secondary transition-colors hover:bg-panel-hover hover:text-ink"
              (click)="onCancel()"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="rounded-lg bg-signal-clear/15 px-5 py-2.5 font-display text-sm font-semibold text-signal-clear ring-1 ring-signal-clear/25 transition-all hover:bg-signal-clear/25 hover:ring-signal-clear/40 hover:shadow-[0_0_16px_var(--color-glow-green)] disabled:opacity-30"
              [disabled]="loading() || saving()"
            >
              {{ saving() ? 'Creating...' : 'Create' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  `,
})
export class CreateServiceDialogComponent implements OnInit {
  private readonly dialogRef = inject(DialogRef<CreateServiceDialogResult>);
  private readonly vehicleService = inject(VehicleService);
  private readonly serviceService = inject(ServiceService);

  readonly vehicles = signal<readonly Vehicle[]>([]);
  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly loadError = signal<string | null>(null);
  readonly createError = signal<string | null>(null);
  readonly submitted = signal(false);

  readonly name = signal('');
  readonly vehicleId = signal('');

  ngOnInit(): void {
    this.vehicleService.getVehicles().subscribe({
      next: (v) => {
        this.vehicles.set(v);
        this.loading.set(false);
      },
      error: () => {
        this.loadError.set('Failed to load vehicles');
        this.loading.set(false);
      },
    });
  }

  onSubmit(): void {
    this.submitted.set(true);
    const n = this.name().trim();
    const vid = this.vehicleId();
    if (!n || !vid) return;

    this.saving.set(true);
    this.createError.set(null);
    this.serviceService.createService({ name: n, vehicle_id: vid }).subscribe({
      next: (res) => {
        this.dialogRef.close({ serviceId: res.id });
      },
      error: (err: HttpErrorResponse) => {
        this.createError.set(extractErrorMessage(err, 'Failed to create service.'));
        this.saving.set(false);
      },
    });
  }

  onCancel(): void {
    this.dialogRef.close();
  }
}
