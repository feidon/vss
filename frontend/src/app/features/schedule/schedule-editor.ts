import { Component, inject, OnInit, signal, viewChild } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ServiceService } from '../../core/services/service.service';
import { ServiceDetailResponse, ConflictResponse } from '../../shared/models';
import { RouteEditorComponent } from './route-editor';
import { ConflictAlertComponent } from './conflict-alert';
import { TrackMapEditorComponent, MapStopEvent } from './track-map-editor';

@Component({
  selector: 'app-schedule-editor',
  imports: [RouterLink, RouteEditorComponent, ConflictAlertComponent, TrackMapEditorComponent],
  template: `
    @if (service()) {
      <div class="mb-4 flex items-center gap-4">
        <a
          routerLink="/schedule"
          class="rounded bg-gray-200 px-4 py-2 text-sm font-medium hover:bg-gray-300"
        >
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
        <div
          class="mb-4 flex items-center justify-between rounded border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800"
        >
          <span>{{ errorMessage() }}</span>
          <button
            class="ml-4 font-medium text-red-600 hover:text-red-800"
            (click)="errorMessage.set(null)"
          >
            Dismiss
          </button>
        </div>
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
      error: (err) => {
        if (err.status === 409) {
          const body = err.error;
          const detail = body?.detail ?? body;
          this.conflicts.set(detail as ConflictResponse);
        } else {
          this.errorMessage.set('Failed to update route. Please try again.');
        }
      },
    });
  }

  onBack(): void {
    this.router.navigate(['/schedule']);
  }
}
