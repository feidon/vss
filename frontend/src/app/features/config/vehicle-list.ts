import { Component, inject, OnInit, signal } from '@angular/core';
import { VehicleService } from '../../core/services/vehicle.service';
import { Vehicle } from '../../shared/models';
import { ErrorAlertComponent } from '../../shared/components/error-alert';

@Component({
  selector: 'app-vehicle-list',
  imports: [ErrorAlertComponent],
  template: `
    <div class="mb-6 animate-fade-in">
      <h2 class="font-display text-3xl font-bold tracking-wide text-ink">Vehicles</h2>
      <p class="mt-0.5 font-display text-base text-ink-muted">Fleet overview</p>
    </div>

    @if (error()) {
      <app-error-alert [message]="error()!" (dismiss)="error.set(null)" />
    }

    @if (loading()) {
      <div class="flex items-center gap-2 text-ink-muted animate-fade-in">
        <svg class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="4"
          ></circle>
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          ></path>
        </svg>
        <span class="font-display text-sm">Loading vehicles...</span>
      </div>
    } @else if (!error()) {
      <div class="card overflow-hidden animate-fade-in delay-1">
        <table class="data-table">
          <thead>
            <tr>
              <th>Name</th>
            </tr>
          </thead>
          <tbody>
            @for (vehicle of vehicles(); track vehicle.id) {
              <tr class="h-10 transition-colors">
                <td class="font-display font-semibold text-ink">{{ vehicle.name }}</td>
              </tr>
            }
          </tbody>
        </table>
      </div>
    }
  `,
})
export class VehicleListComponent implements OnInit {
  private readonly vehicleService = inject(VehicleService);

  readonly vehicles = signal<readonly Vehicle[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  ngOnInit(): void {
    this.vehicleService.getVehicles().subscribe({
      next: (vehicles) => {
        this.vehicles.set(
          [...vehicles].sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true })),
        );
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Failed to load vehicles.');
        this.loading.set(false);
      },
    });
  }
}
