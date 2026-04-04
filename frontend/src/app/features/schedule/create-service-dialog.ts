import { Component, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DialogRef } from '@angular/cdk/dialog';
import { VehicleService } from '../../core/services/vehicle.service';
import { ServiceService } from '../../core/services/service.service';
import { Vehicle } from '../../shared/models';

export interface CreateServiceDialogResult {
  readonly serviceId: number;
}

@Component({
  selector: 'app-create-service-dialog',
  imports: [FormsModule],
  template: `
    <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div class="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h3 class="mb-4 text-lg font-semibold">Create Service</h3>

        @if (loadError()) {
          <p class="mb-4 text-sm text-red-600">{{ loadError() }}</p>
        }

        <form (ngSubmit)="onSubmit()">
          <div class="mb-4">
            <label class="mb-1 block text-sm font-medium text-gray-700" for="dlg-name">
              Name
            </label>
            <input
              id="dlg-name"
              class="w-full rounded border px-3 py-2 text-sm"
              [(ngModel)]="name"
              name="name"
              placeholder="e.g. S101"
              required
            />
            @if (submitted() && !name().trim()) {
              <p class="mt-1 text-xs text-red-500">Name is required</p>
            }
          </div>

          <div class="mb-6">
            <label class="mb-1 block text-sm font-medium text-gray-700" for="dlg-vehicle">
              Vehicle
            </label>
            <select
              id="dlg-vehicle"
              class="w-full rounded border px-3 py-2 text-sm"
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
              <p class="mt-1 text-xs text-red-500">Vehicle is required</p>
            }
          </div>

          <div class="flex justify-end gap-3">
            <button
              type="button"
              class="rounded border px-4 py-2 text-sm hover:bg-gray-100"
              (click)="onCancel()"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="rounded bg-green-600 px-4 py-2 text-sm text-white hover:bg-green-700 disabled:opacity-50"
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
    this.serviceService.createService({ name: n, vehicle_id: vid }).subscribe({
      next: (res) => {
        this.dialogRef.close({ serviceId: res.id });
      },
      error: () => {
        this.saving.set(false);
      },
    });
  }

  onCancel(): void {
    this.dialogRef.close();
  }
}
