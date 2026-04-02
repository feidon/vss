import { Component, inject, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Vehicle } from '../../shared/models';
import { ServiceService } from '../../core/services/service.service';

@Component({
  selector: 'app-service-form',
  imports: [FormsModule],
  template: `
    <form class="mb-6 flex items-end gap-3" (ngSubmit)="onSubmit()">
      <div>
        <label class="mb-1 block text-xs text-gray-600" for="service-name">Name</label>
        <input
          id="service-name"
          class="rounded border px-2 py-1 text-sm"
          [(ngModel)]="name"
          name="name"
          placeholder="e.g. S101"
          required
        />
      </div>
      <div>
        <label class="mb-1 block text-xs text-gray-600" for="vehicle-select">Vehicle</label>
        <select
          id="vehicle-select"
          class="rounded border px-2 py-1 text-sm"
          [(ngModel)]="vehicleId"
          name="vehicleId"
          required
        >
          <option value="" disabled>Select vehicle</option>
          @for (v of vehicles(); track v.id) {
            <option [value]="v.id">{{ v.name }}</option>
          }
        </select>
      </div>
      <button
        type="submit"
        class="rounded bg-green-600 px-3 py-1 text-sm text-white hover:bg-green-700 disabled:opacity-50"
        [disabled]="!name() || !vehicleId()"
      >
        Create Service
      </button>
    </form>
  `,
})
export class ServiceFormComponent {
  private readonly serviceService = inject(ServiceService);

  readonly vehicles = input.required<readonly Vehicle[]>();
  readonly created = output<number>();

  readonly name = signal('');
  readonly vehicleId = signal('');

  onSubmit(): void {
    const n = this.name().trim();
    const vid = this.vehicleId();
    if (!n || !vid) return;

    this.serviceService.createService({ name: n, vehicle_id: vid }).subscribe((res) => {
      this.name.set('');
      this.vehicleId.set('');
      this.created.emit(res.id);
    });
  }
}
