import { Component, inject, OnInit, signal } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';
import { Dialog } from '@angular/cdk/dialog';
import { ServiceService } from '../../core/services/service.service';
import { ServiceDetailResponse, ServiceResponse } from '../../shared/models';
import { ErrorAlertComponent } from '../../shared/components/error-alert';
import { extractErrorMessage } from '../../shared/utils/error-utils';
import { EpochTimePipe } from '../../shared/pipes/epoch-time.pipe';
import { CreateServiceDialogComponent, CreateServiceDialogResult } from './create-service-dialog';

@Component({
  selector: 'app-schedule-list',
  imports: [EpochTimePipe, ErrorAlertComponent],
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

    @if (errorMessage()) {
      <app-error-alert [message]="errorMessage()!" (dismiss)="errorMessage.set(null)" />
    }

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
            <tr class="cursor-pointer border-b hover:bg-gray-50" (click)="toggleExpand(service)">
              <td class="px-3 py-2 font-medium">{{ service.name }}</td>
              <td class="px-3 py-2">{{ service.vehicle_name }}</td>
              <td class="px-3 py-2">
                {{ service.start_time ? (service.start_time | epochTime) : '—' }}
              </td>
              <td class="px-3 py-2">{{ service.origin_name ?? '—' }}</td>
              <td class="px-3 py-2">{{ service.destination_name ?? '—' }}</td>
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
            @if (expandedServiceId() === service.id) {
              <tr class="border-b bg-gray-50">
                <td colspan="6" class="px-6 py-3 text-sm text-gray-600">
                  @if (!detailCache().has(service.id)) {
                    Loading...
                  } @else if (detailCache().get(service.id)!.route.length === 0) {
                    No route defined
                  } @else {
                    {{ routePath(service.id) }}
                  }
                </td>
              </tr>
            }
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
  readonly errorMessage = signal<string | null>(null);
  readonly expandedServiceId = signal<number | null>(null);
  readonly detailCache = signal<ReadonlyMap<number, ServiceDetailResponse>>(new Map());

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
    this.serviceService.deleteService(service.id).subscribe({
      next: () => this.loadServices(),
      error: (err: HttpErrorResponse) =>
        this.errorMessage.set(extractErrorMessage(err, 'Failed to delete service.')),
    });
  }

  toggleExpand(service: ServiceResponse): void {
    if (this.expandedServiceId() === service.id) {
      this.expandedServiceId.set(null);
      return;
    }
    this.expandedServiceId.set(service.id);
    if (!this.detailCache().has(service.id)) {
      this.serviceService.getService(service.id).subscribe({
        next: (detail) => {
          const updated = new Map(this.detailCache());
          updated.set(service.id, detail);
          this.detailCache.set(updated);
        },
        error: (err: HttpErrorResponse) =>
          this.errorMessage.set(extractErrorMessage(err, 'Failed to load service details.')),
      });
    }
  }

  routePath(serviceId: number): string {
    const detail = this.detailCache().get(serviceId);
    if (!detail) return '';
    return detail.route.map((node) => node.name).join(' → ');
  }

  private loadServices(): void {
    this.serviceService.getServices().subscribe({
      next: (s) => {
        this.services.set(s);
        this.expandedServiceId.set(null);
        this.detailCache.set(new Map());
      },
      error: (err: HttpErrorResponse) =>
        this.errorMessage.set(extractErrorMessage(err, 'Failed to load services.')),
    });
  }
}
