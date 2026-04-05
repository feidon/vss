import { Component, DestroyRef, inject, OnInit, signal } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Router } from '@angular/router';
import { Dialog } from '@angular/cdk/dialog';
import { ServiceService } from '../../core/services/service.service';
import { ServiceDetailResponse, ServiceResponse } from '../../shared/models';
import { ErrorAlertComponent } from '../../shared/components/error-alert';
import { ConfirmDialogComponent, ConfirmDialogData } from '../../shared/components/confirm-dialog';
import { extractErrorMessage } from '../../shared/utils/error-utils';
import { EpochTimePipe } from '../../shared/pipes/epoch-time.pipe';
import { CreateServiceDialogComponent, CreateServiceDialogResult } from './create-service-dialog';
import { AutoScheduleDialogComponent, AutoScheduleDialogResult } from './auto-schedule-dialog';

@Component({
  selector: 'app-schedule-list',
  imports: [EpochTimePipe, ErrorAlertComponent],
  template: `
    <div class="mb-6 flex items-center justify-between animate-fade-in">
      <div>
        <h2 class="font-display text-3xl font-bold tracking-wide text-ink">Schedule</h2>
        <p class="mt-0.5 font-display text-base text-ink-muted">Service route management</p>
      </div>
      <div class="flex items-center gap-3">
        <button
          class="flex items-center gap-2 rounded-lg bg-signal-caution/10 px-4 py-2.5 font-display text-base font-semibold text-signal-caution ring-1 ring-signal-caution/25 transition-all hover:bg-signal-caution/20 hover:ring-signal-caution/40"
          (click)="onAutoSchedule()"
        >
          <svg
            class="h-4 w-4"
            viewBox="0 0 16 16"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M2 8h3l2-5 3 10 2-5h3" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          Auto Schedule
        </button>
        <button
          class="flex items-center gap-2 rounded-lg bg-signal-clear/10 px-4 py-2.5 font-display text-base font-semibold text-signal-clear ring-1 ring-signal-clear/25 transition-all hover:bg-signal-clear/20 hover:ring-signal-clear/40 hover:shadow-[0_0_16px_var(--color-glow-green)]"
          (click)="onCreateService()"
        >
          <svg
            class="h-4 w-4"
            viewBox="0 0 16 16"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M8 3v10M3 8h10" />
          </svg>
          Create Service
        </button>
      </div>
    </div>

    @if (errorMessage()) {
      <app-error-alert [message]="errorMessage()!" (dismiss)="errorMessage.set(null)" />
    }

    @if (services().length === 0) {
      <div class="card flex flex-col items-center justify-center py-16 animate-fade-in">
        <div
          class="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-panel-raised ring-1 ring-edge"
        >
          <svg
            class="h-6 w-6 text-ink-muted"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.5"
          >
            <path d="M9 6h11M9 12h11M9 18h7M4 6h.01M4 12h.01M4 18h.01" stroke-linecap="round" />
          </svg>
        </div>
        <p class="font-display text-base text-ink-muted">No services created yet</p>
        <p class="mt-1 text-sm text-ink-muted/60">Click "Create Service" to get started</p>
      </div>
    } @else {
      <div class="card overflow-hidden animate-fade-in delay-1">
        <table class="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Vehicle</th>
              <th>Start Time</th>
              <th>Origin</th>
              <th>Destination</th>
              <th class="text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            @for (service of services(); track service.id) {
              <tr class="cursor-pointer transition-colors" (click)="toggleExpand(service)">
                <td class="font-display font-semibold text-ink">{{ service.name }}</td>
                <td>
                  <span
                    class="inline-flex items-center gap-1.5 rounded-md bg-signal-info/10 px-2 py-0.5 text-sm font-medium text-signal-info ring-1 ring-signal-info/20"
                  >
                    {{ service.vehicle_name }}
                  </span>
                </td>
                <td class="font-mono text-sm">
                  {{ service.start_time ? (service.start_time | epochTime) : '-' }}
                </td>
                <td>{{ service.origin_name ?? '-' }}</td>
                <td>{{ service.destination_name ?? '-' }}</td>
                <td class="text-right">
                  <div class="flex items-center justify-end gap-1.5">
                    <button
                      class="rounded-md p-1.5 text-ink-muted transition-colors hover:bg-signal-info/10 hover:text-signal-info"
                      title="Edit"
                      (click)="onEdit(service); $event.stopPropagation()"
                    >
                      <svg class="h-3.5 w-3.5" viewBox="0 0 16 16" fill="currentColor">
                        <path
                          d="M11.013 1.427a1.75 1.75 0 012.474 0l1.086 1.086a1.75 1.75 0 010 2.474l-8.61 8.61c-.21.21-.47.364-.756.445l-3.251.93a.75.75 0 01-.927-.928l.929-3.25a1.75 1.75 0 01.445-.758l8.61-8.61z"
                        />
                      </svg>
                    </button>
                    <button
                      class="rounded-md p-1.5 text-ink-muted transition-colors hover:bg-signal-danger/10 hover:text-signal-danger"
                      title="Delete"
                      (click)="onDelete(service); $event.stopPropagation()"
                    >
                      <svg class="h-3.5 w-3.5" viewBox="0 0 16 16" fill="currentColor">
                        <path
                          d="M5.75 1a.75.75 0 00-.75.75V3H2a.75.75 0 000 1.5h.75l.573 8.583A1.75 1.75 0 005.07 14.75h5.86a1.75 1.75 0 001.747-1.667L13.25 4.5H14A.75.75 0 0014 3h-3V1.75A.75.75 0 0010.25 1h-4.5zM6.5 3V2.5h3V3h-3z"
                        />
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
              @if (expandedServiceId() === service.id) {
                <tr>
                  <td colspan="6" class="!border-b-edge bg-panel-raised/50 px-6 py-3">
                    <div class="flex items-center gap-2 font-mono text-sm text-ink-secondary">
                      @if (!detailCache().has(service.id)) {
                        <span
                          class="inline-block h-4 w-4 animate-spin rounded-full border-2 border-ink-muted border-t-signal-info"
                        ></span>
                        Loading...
                      } @else if (detailCache().get(service.id)!.route.length === 0) {
                        <span class="text-ink-muted">No route defined</span>
                      } @else {
                        <svg
                          class="h-3.5 w-3.5 shrink-0 text-signal-clear"
                          viewBox="0 0 16 16"
                          fill="currentColor"
                        >
                          <path
                            d="M8 0a8 8 0 100 16A8 8 0 008 0zm3.28 5.78l-4 4a.75.75 0 01-1.06 0l-2-2a.75.75 0 011.06-1.06L6.5 8.19l3.47-3.47a.75.75 0 011.06 1.06z"
                          />
                        </svg>
                        {{ routePath(service.id) }}
                      }
                    </div>
                  </td>
                </tr>
              }
            }
          </tbody>
        </table>
      </div>
    }
  `,
})
export class ScheduleListComponent implements OnInit {
  private readonly serviceService = inject(ServiceService);
  private readonly router = inject(Router);
  private readonly dialog = inject(Dialog);
  private readonly destroyRef = inject(DestroyRef);

  readonly services = signal<readonly ServiceResponse[]>([]);
  readonly errorMessage = signal<string | null>(null);
  readonly expandedServiceId = signal<number | null>(null);
  readonly detailCache = signal<ReadonlyMap<number, ServiceDetailResponse>>(new Map());

  ngOnInit(): void {
    this.loadServices();
  }

  onCreateService(): void {
    const ref = this.dialog.open<CreateServiceDialogResult>(CreateServiceDialogComponent);
    ref.closed.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((result) => {
      if (result) {
        this.router.navigate(['/schedule', result.serviceId, 'edit']);
      }
    });
  }

  onAutoSchedule(): void {
    const ref = this.dialog.open<AutoScheduleDialogResult>(AutoScheduleDialogComponent);
    ref.closed.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((result) => {
      if (result) {
        this.loadServices();
      }
    });
  }

  onEdit(service: ServiceResponse): void {
    this.router.navigate(['/schedule', service.id, 'edit']);
  }

  onDelete(service: ServiceResponse): void {
    const ref = this.dialog.open<boolean, ConfirmDialogData>(ConfirmDialogComponent, {
      data: { message: `Delete service "${service.name}"?` },
    });
    ref.closed.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((confirmed) => {
      if (!confirmed) return;
      this.serviceService.deleteService(service.id).subscribe({
        next: () => this.loadServices(),
        error: (err: HttpErrorResponse) =>
          this.errorMessage.set(extractErrorMessage(err, 'Failed to delete service.')),
      });
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
