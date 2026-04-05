import { Component, inject, OnInit, signal, viewChild } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { switchMap } from 'rxjs';
import { ServiceService } from '../../core/services/service.service';
import { ServiceDetailResponse, ConflictResponse } from '../../shared/models';
import { ErrorAlertComponent } from '../../shared/components/error-alert';
import { extractErrorMessage } from '../../shared/utils/error-utils';
import { RouteEditorComponent } from './route-editor';
import { ConflictAlertComponent } from './conflict-alert';
import { TrackMapEditorComponent, MapStopEvent } from './track-map-editor';

@Component({
  selector: 'app-schedule-editor',
  imports: [
    RouterLink,
    RouteEditorComponent,
    ConflictAlertComponent,
    TrackMapEditorComponent,
    ErrorAlertComponent,
  ],
  template: `
    @if (service()) {
      <div class="mb-6 animate-fade-in">
        <a
          routerLink="/schedule"
          class="group mb-2 inline-flex items-center gap-1.5 font-display text-base text-ink-muted transition-colors hover:text-signal-info"
        >
          <svg
            class="h-3.5 w-3.5 transition-transform group-hover:-translate-x-0.5"
            viewBox="0 0 16 16"
            fill="currentColor"
          >
            <path
              fill-rule="evenodd"
              d="M9.78 4.22a.75.75 0 010 1.06L7.06 8l2.72 2.72a.75.75 0 11-1.06 1.06L5.47 8.53a.75.75 0 010-1.06l3.25-3.25a.75.75 0 011.06 0z"
            />
          </svg>
          Back to Schedule
        </a>
        <h2 class="font-display text-3xl font-bold tracking-wide text-ink">
          Edit {{ service()!.name }}
        </h2>
        <p class="mt-0.5 font-display text-base text-ink-muted">Route &amp; timetable editor</p>
      </div>

      @if (conflicts()) {
        <app-conflict-alert
          [conflicts]="conflicts()!"
          [graph]="service()!.graph"
          (dismiss)="conflicts.set(null)"
        />
      }

      @if (errorMessage()) {
        <app-error-alert [message]="errorMessage()!" (dismiss)="errorMessage.set(null)" />
      }

      <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div class="card overflow-hidden animate-fade-in delay-1">
          <div class="border-b border-edge px-4 py-3">
            <h3
              class="font-display text-base font-semibold uppercase tracking-wider text-ink-muted"
            >
              Track Map
            </h3>
          </div>
          <app-track-map-editor
            [graph]="service()!.graph"
            [queuedNodeIds]="queuedNodeIds()"
            (stopAdded)="onMapStopAdded($event)"
          />
        </div>
        <div class="card overflow-hidden animate-fade-in delay-2">
          <div class="border-b border-edge px-4 py-3">
            <h3
              class="font-display text-base font-semibold uppercase tracking-wider text-ink-muted"
            >
              Route Editor
            </h3>
          </div>
          <div class="p-4">
            <app-route-editor
              [service]="service()!"
              [graph]="service()!.graph"
              (submitted)="onRouteSubmitted($event)"
              (stopsChanged)="onStopsChanged($event)"
            />
          </div>
        </div>
      </div>
    } @else {
      <div class="flex items-center gap-3 py-12 justify-center">
        <span
          class="inline-block h-5 w-5 animate-spin rounded-full border-2 border-ink-muted border-t-signal-info"
        ></span>
        <span class="font-display text-base text-ink-muted">Loading service...</span>
      </div>
    }
  `,
})
export class ScheduleEditorComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly serviceService = inject(ServiceService);

  private readonly routeEditor = viewChild(RouteEditorComponent);

  readonly service = signal<ServiceDetailResponse | null>(null);
  readonly conflicts = signal<ConflictResponse | null>(null);
  readonly errorMessage = signal<string | null>(null);
  readonly queuedNodeIds = signal<readonly string[]>([]);

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.serviceService.getService(id).subscribe({
      next: (s) => this.service.set(s),
      error: (err: HttpErrorResponse) =>
        this.errorMessage.set(extractErrorMessage(err, 'Failed to load service.')),
    });
  }

  onMapStopAdded(event: MapStopEvent): void {
    this.routeEditor()?.addStopFromMap(event.nodeId, event.nodeName);
  }

  onStopsChanged(nodeIds: readonly string[]): void {
    this.queuedNodeIds.set(nodeIds);
  }

  onRouteSubmitted(request: {
    stops: { node_id: string; dwell_time: number }[];
    start_time: number;
  }): void {
    const id = this.service()!.id;
    this.conflicts.set(null);
    this.errorMessage.set(null);
    this.serviceService
      .updateRoute(id, request)
      .pipe(switchMap(() => this.serviceService.getService(id)))
      .subscribe({
        next: (s) => this.service.set(s),
        error: (err: HttpErrorResponse) => {
          if (err.status === 409) {
            const body = err.error;
            const detail = body?.detail ?? body;
            if (detail && 'vehicle_conflicts' in detail && 'block_conflicts' in detail) {
              this.conflicts.set(detail as ConflictResponse);
            } else {
              this.errorMessage.set('Conflict detected but response format was unexpected.');
            }
          } else {
            this.errorMessage.set(
              extractErrorMessage(err, 'Failed to update route. Please try again.'),
            );
          }
        },
      });
  }
}
