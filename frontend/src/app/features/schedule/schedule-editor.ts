import { Component, inject, OnInit, signal, viewChild } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
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
      <div class="mb-4">
        <a routerLink="/schedule" class="text-sm text-gray-500 hover:text-gray-700">
          &larr; Back to Schedule
        </a>
        <h2 class="text-xl font-semibold">{{ service()!.name }}</h2>
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
        <div>
          <app-track-map-editor
            [graph]="service()!.graph"
            [queuedNodeIds]="queuedNodeIds()"
            (stopAdded)="onMapStopAdded($event)"
          />
        </div>
        <div>
          <app-route-editor
            [service]="service()!"
            [graph]="service()!.graph"
            (submitted)="onRouteSubmitted($event)"
            (back)="onBack()"
            (stopsChanged)="onStopsChanged($event)"
          />
        </div>
      </div>
    } @else {
      <p class="py-4 text-gray-500">Loading service...</p>
    }
  `,
})
export class ScheduleEditorComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly serviceService = inject(ServiceService);

  private readonly routeEditor = viewChild(RouteEditorComponent);

  readonly service = signal<ServiceDetailResponse | null>(null);
  readonly conflicts = signal<ConflictResponse | null>(null);
  readonly errorMessage = signal<string | null>(null);
  readonly queuedNodeIds = signal<readonly string[]>([]);

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.serviceService.getService(id).subscribe((s) => this.service.set(s));
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
    this.serviceService.updateRoute(id, request).subscribe({
      next: () => {
        this.serviceService.getService(id).subscribe((s) => this.service.set(s));
      },
      error: (err: HttpErrorResponse) => {
        if (err.status === 409) {
          const body = err.error;
          const detail = body?.detail ?? body;
          this.conflicts.set(detail as ConflictResponse);
        } else {
          this.errorMessage.set(
            extractErrorMessage(err, 'Failed to update route. Please try again.'),
          );
        }
      },
    });
  }

  onBack(): void {
    this.router.navigate(['/schedule']);
  }
}
