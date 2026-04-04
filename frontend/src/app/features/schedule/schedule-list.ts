import { Component, inject, OnInit, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Dialog } from '@angular/cdk/dialog';
import { ServiceService } from '../../core/services/service.service';
import { ServiceResponse } from '../../shared/models';
import { EpochTimePipe } from '../../shared/pipes/epoch-time.pipe';
import { CreateServiceDialogComponent, CreateServiceDialogResult } from './create-service-dialog';

@Component({
  selector: 'app-schedule-list',
  imports: [EpochTimePipe],
  template: `
    <div class="mb-4 flex items-center justify-between">
      <h2 class="text-xl font-semibold">Schedule</h2>
      <button
        class="rounded bg-green-600 px-4 py-2 text-sm text-white hover:bg-green-700"
        (click)="onCreateService()"
      >
        + Create Service
      </button>
    </div>

    @if (services().length === 0) {
      <p class="py-4 text-gray-500">No services created yet.</p>
    } @else {
      <table class="w-full text-left text-sm">
        <thead class="border-b text-xs uppercase text-gray-500">
          <tr>
            <th class="px-3 py-2">Name</th>
            <th class="px-3 py-2">Vehicle</th>
            <th class="px-3 py-2">Start Time</th>
            <th class="px-3 py-2">Origin</th>
            <th class="px-3 py-2">Destination</th>
            <th class="px-3 py-2">Actions</th>
          </tr>
        </thead>
        <tbody>
          @for (service of services(); track service.id) {
            <tr class="border-b hover:bg-gray-50">
              <td class="px-3 py-2 font-medium">{{ service.name }}</td>
              <td class="px-3 py-2">{{ service.vehicle_name }}</td>
              <td class="px-3 py-2">
                {{ service.start_time ? (service.start_time | epochTime) : '—' }}
              </td>
              <td class="px-3 py-2">{{ service.origin ?? '—' }}</td>
              <td class="px-3 py-2">{{ service.destination ?? '—' }}</td>
              <td class="flex gap-2 px-3 py-2">
                <button
                  class="rounded bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-700"
                  (click)="onEdit(service); $event.stopPropagation()"
                >
                  Edit
                </button>
                <button
                  class="rounded bg-red-600 px-2 py-1 text-xs text-white hover:bg-red-700"
                  (click)="onDelete(service); $event.stopPropagation()"
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
export class ScheduleListComponent implements OnInit {
  private readonly serviceService = inject(ServiceService);
  private readonly router = inject(Router);
  private readonly dialog = inject(Dialog);

  readonly services = signal<readonly ServiceResponse[]>([]);

  ngOnInit(): void {
    this.loadServices();
  }

  onCreateService(): void {
    const ref = this.dialog.open<CreateServiceDialogResult>(CreateServiceDialogComponent);
    ref.closed.subscribe((result) => {
      if (result) {
        this.router.navigate(['/schedule', result.serviceId, 'edit']);
      }
    });
  }

  onEdit(service: ServiceResponse): void {
    this.router.navigate(['/schedule', service.id, 'edit']);
  }

  onDelete(service: ServiceResponse): void {
    if (!window.confirm(`Delete service "${service.name}"?`)) return;
    this.serviceService.deleteService(service.id).subscribe(() => this.loadServices());
  }

  private loadServices(): void {
    this.serviceService.getServices().subscribe((s) => this.services.set(s));
  }
}
