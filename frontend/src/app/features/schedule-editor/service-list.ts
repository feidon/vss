import { Component, input, output } from '@angular/core';
import { ServiceResponse, Vehicle } from '../../shared/models';

@Component({
  selector: 'app-service-list',
  template: `
    @if (services().length === 0) {
      <p class="py-4 text-gray-500">No services created yet.</p>
    } @else {
      <table class="mt-4 w-full text-left text-sm">
        <thead class="border-b text-xs uppercase text-gray-500">
          <tr>
            <th class="px-3 py-2">Name</th>
            <th class="px-3 py-2">Vehicle</th>
            <th class="px-3 py-2">Actions</th>
          </tr>
        </thead>
        <tbody>
          @for (service of services(); track service.id) {
            <tr class="border-b">
              <td class="px-3 py-2 font-medium">{{ service.name }}</td>
              <td class="px-3 py-2">{{ vehicleName(service.vehicle_id) }}</td>
              <td class="flex gap-2 px-3 py-2">
                <button
                  class="rounded bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-700"
                  (click)="edit.emit(service)"
                >
                  Edit
                </button>
                <button
                  class="rounded bg-red-600 px-2 py-1 text-xs text-white hover:bg-red-700"
                  (click)="delete.emit(service)"
                >
                  Delete
                </button>
              </td>
            </tr>
          }
        </tbody>
      </table>
    }
  `,
})
export class ServiceListComponent {
  readonly services = input.required<readonly ServiceResponse[]>();
  readonly vehicles = input.required<readonly Vehicle[]>();
  readonly edit = output<ServiceResponse>();
  readonly delete = output<ServiceResponse>();

  vehicleName(vehicleId: string): string {
    return this.vehicles().find((v) => v.id === vehicleId)?.name ?? vehicleId;
  }
}
