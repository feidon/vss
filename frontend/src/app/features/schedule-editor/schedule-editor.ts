import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { ServiceService } from '../../core/services/service.service';
import { GraphService } from '../../core/services/graph.service';
import { ServiceResponse, GraphResponse, ConflictResponse, Vehicle } from '../../shared/models';
import { ServiceListComponent } from './service-list';
import { ServiceFormComponent } from './service-form';
import { RouteEditorComponent } from './route-editor';
import { ConflictAlertComponent } from './conflict-alert';

type ViewMode = 'list' | 'edit';

@Component({
  selector: 'app-schedule-editor',
  imports: [
    ServiceListComponent,
    ServiceFormComponent,
    RouteEditorComponent,
    ConflictAlertComponent,
  ],
  template: `
    <h2 class="mb-4 text-xl font-semibold">Schedule Editor</h2>

    @if (viewMode() === 'list') {
      <app-service-form [vehicles]="vehicles()" (created)="onServiceCreated($event)" />
      <app-service-list
        [services]="services()"
        [vehicles]="vehicles()"
        (edit)="onEdit($event)"
        (delete)="onDelete($event)"
      />
    } @else {
      @if (conflicts()) {
        <app-conflict-alert [conflicts]="conflicts()!" (dismiss)="conflicts.set(null)" />
      }
      <app-route-editor
        [service]="selectedService()!"
        [graph]="graph()!"
        (submitted)="onRouteSubmitted($event)"
        (back)="onBackToList()"
      />
    }
  `,
})
export class ScheduleEditorComponent implements OnInit {
  private readonly serviceService = inject(ServiceService);
  private readonly graphService = inject(GraphService);

  readonly services = signal<readonly ServiceResponse[]>([]);
  readonly graph = signal<GraphResponse | null>(null);
  readonly selectedService = signal<ServiceResponse | null>(null);
  readonly conflicts = signal<ConflictResponse | null>(null);
  readonly viewMode = signal<ViewMode>('list');

  readonly vehicles = computed<readonly Vehicle[]>(() => this.graph()?.vehicles ?? []);

  ngOnInit(): void {
    this.loadServices();
    this.graphService.getGraph().subscribe((g) => this.graph.set(g));
  }

  onEdit(service: ServiceResponse): void {
    this.selectedService.set(service);
    this.conflicts.set(null);
    this.viewMode.set('edit');
  }

  onDelete(service: ServiceResponse): void {
    if (!window.confirm(`Delete service "${service.name}"?`)) return;
    this.serviceService.deleteService(service.id).subscribe(() => this.loadServices());
  }

  onServiceCreated(serviceId: number): void {
    this.serviceService.getService(serviceId).subscribe((s) => {
      this.loadServices();
      this.selectedService.set(s);
      this.conflicts.set(null);
      this.viewMode.set('edit');
    });
  }

  onRouteSubmitted(request: {
    stops: { platform_id: string; dwell_time: number }[];
    start_time: number;
  }): void {
    const id = this.selectedService()!.id;
    this.conflicts.set(null);
    this.serviceService.updateRoute(id, request).subscribe({
      next: () => {
        this.serviceService.getService(id).subscribe((s) => {
          this.selectedService.set(s);
          this.loadServices();
        });
      },
      error: (err) => {
        if (err.status === 409) {
          this.conflicts.set(err.error.detail as ConflictResponse);
        }
      },
    });
  }

  onBackToList(): void {
    this.selectedService.set(null);
    this.conflicts.set(null);
    this.viewMode.set('list');
    this.loadServices();
  }

  private loadServices(): void {
    this.serviceService.getServices().subscribe((s) => this.services.set(s));
  }
}
