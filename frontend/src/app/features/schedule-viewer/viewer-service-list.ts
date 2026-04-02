import { Component, computed, input, output, signal } from '@angular/core';
import { NgTemplateOutlet } from '@angular/common';
import { ServiceResponse, Vehicle } from '../../shared/models';

interface VehicleGroup {
  readonly vehicleName: string;
  readonly services: readonly ServiceResponse[];
}

@Component({
  selector: 'app-viewer-service-list',
  imports: [NgTemplateOutlet],
  template: `
    <div class="mb-4 flex items-center gap-4">
      <select
        class="rounded border border-gray-300 px-3 py-1.5 text-sm"
        [value]="vehicleFilter()"
        (change)="onFilterChange($event)"
      >
        <option value="">All vehicles</option>
        @for (vehicle of vehicles(); track vehicle.id) {
          <option [value]="vehicle.id">{{ vehicle.name }}</option>
        }
      </select>

      <label class="flex items-center gap-1.5 text-sm">
        <input
          type="checkbox"
          [checked]="grouped()"
          (change)="grouped.set(!grouped())"
          class="rounded"
        />
        Group by vehicle
      </label>
    </div>

    @if (filteredServices().length === 0) {
      <p class="py-4 text-gray-500">No services to display.</p>
    } @else if (grouped()) {
      @for (group of groupedServices(); track group.vehicleName) {
        <h3 class="mt-4 mb-2 text-sm font-semibold text-gray-700">
          {{ group.vehicleName }}
        </h3>
        <ng-container
          *ngTemplateOutlet="serviceTable; context: { $implicit: group.services }"
        />
      }
    } @else {
      <ng-container
        *ngTemplateOutlet="serviceTable; context: { $implicit: filteredServices() }"
      />
    }

    <ng-template #serviceTable let-items>
      <table class="w-full text-left text-sm">
        <thead class="border-b text-xs uppercase text-gray-500">
          <tr>
            <th class="px-3 py-2">Name</th>
            <th class="px-3 py-2">Vehicle</th>
            <th class="px-3 py-2">Stops</th>
          </tr>
        </thead>
        <tbody>
          @for (service of items; track service.id) {
            <tr
              class="cursor-pointer border-b hover:bg-gray-50"
              (click)="select.emit(service)"
            >
              <td class="px-3 py-2 font-medium">{{ service.name }}</td>
              <td class="px-3 py-2">{{ vehicleName(service.vehicle_id) }}</td>
              <td class="px-3 py-2">{{ stopCount(service) }}</td>
            </tr>
          }
        </tbody>
      </table>
    </ng-template>
  `,
})
export class ViewerServiceListComponent {
  readonly services = input.required<readonly ServiceResponse[]>();
  readonly vehicles = input.required<readonly Vehicle[]>();
  readonly select = output<ServiceResponse>();

  readonly vehicleFilter = signal('');
  readonly grouped = signal(false);

  readonly filteredServices = computed(() => {
    const filter = this.vehicleFilter();
    const all = this.services();
    return filter ? all.filter((s) => s.vehicle_id === filter) : all;
  });

  readonly groupedServices = computed<readonly VehicleGroup[]>(() => {
    const services = this.filteredServices();
    const vehicles = this.vehicles();
    const groups = new Map<string, ServiceResponse[]>();

    for (const service of services) {
      const list = groups.get(service.vehicle_id) ?? [];
      groups.set(service.vehicle_id, [...list, service]);
    }

    return [...groups.entries()].map(([vehicleId, svcList]) => ({
      vehicleName: vehicles.find((v) => v.id === vehicleId)?.name ?? vehicleId,
      services: svcList,
    }));
  });

  vehicleName(vehicleId: string): string {
    return this.vehicles().find((v) => v.id === vehicleId)?.name ?? vehicleId;
  }

  stopCount(service: ServiceResponse): number {
    return service.path.filter((n) => n.type === 'platform').length;
  }

  onFilterChange(event: Event): void {
    const value = (event.target as HTMLSelectElement).value;
    this.vehicleFilter.set(value);
  }
}
