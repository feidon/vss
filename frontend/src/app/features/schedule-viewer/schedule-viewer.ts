import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { ServiceService } from '../../core/services/service.service';
import { GraphService } from '../../core/services/graph.service';
import { ServiceResponse, GraphResponse, Vehicle } from '../../shared/models';
import { ViewerServiceListComponent } from './viewer-service-list';
import { TimetableDetailComponent } from './timetable-detail';

@Component({
  selector: 'app-schedule-viewer',
  imports: [ViewerServiceListComponent, TimetableDetailComponent],
  template: `
    <h2 class="mb-4 text-xl font-semibold">Schedule Viewer</h2>

    @if (selectedService()) {
      <app-timetable-detail
        [service]="selectedService()!"
        [vehicleName]="selectedVehicleName()"
        (back)="onBackToList()"
      />
    } @else {
      <app-viewer-service-list
        [services]="services()"
        [vehicles]="vehicles()"
        (serviceSelect)="onSelectService($event)"
      />
    }
  `,
})
export class ScheduleViewerComponent implements OnInit {
  private readonly serviceService = inject(ServiceService);
  private readonly graphService = inject(GraphService);

  readonly services = signal<readonly ServiceResponse[]>([]);
  readonly graph = signal<GraphResponse | null>(null);
  readonly selectedService = signal<ServiceResponse | null>(null);

  readonly vehicles = computed<readonly Vehicle[]>(() => this.graph()?.vehicles ?? []);

  readonly selectedVehicleName = computed(() => {
    const service = this.selectedService();
    if (!service) return '';
    return this.vehicles().find((v) => v.id === service.vehicle_id)?.name ?? service.vehicle_id;
  });

  ngOnInit(): void {
    this.serviceService.getServices().subscribe((s) => this.services.set(s));
    this.graphService.getGraph().subscribe((g) => this.graph.set(g));
  }

  onSelectService(service: ServiceResponse): void {
    this.selectedService.set(service);
  }

  onBackToList(): void {
    this.selectedService.set(null);
  }
}
