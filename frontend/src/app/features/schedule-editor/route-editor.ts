import { Component, computed, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ServiceResponse, GraphResponse, Station } from '../../shared/models';

interface StopEntry {
  readonly platformId: string;
  readonly platformName: string;
  readonly dwellTime: number;
}

@Component({
  selector: 'app-route-editor',
  imports: [FormsModule],
  template: `
    <div class="mb-4 flex items-center justify-between">
      <h3 class="text-lg font-medium">Route: {{ service().name }}</h3>
      <button class="rounded border px-3 py-1 text-sm hover:bg-gray-100" (click)="back.emit()">
        Back to list
      </button>
    </div>

    <!-- Stop picker -->
    <div class="mb-4">
      <h4 class="mb-2 text-sm font-medium text-gray-600">Platform Stops</h4>
      <div class="mb-2 flex items-center gap-2">
        <select class="rounded border px-2 py-1 text-sm" [(ngModel)]="selectedPlatformId">
          <option value="">Add a stop...</option>
          @for (station of nonYardStations(); track station.id) {
            <optgroup [label]="station.name">
              @for (pid of station.platform_ids; track pid) {
                <option [value]="pid">{{ platformName(pid) }}</option>
              }
            </optgroup>
          }
        </select>
        <button
          class="rounded bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-700 disabled:opacity-50"
          [disabled]="!selectedPlatformId()"
          (click)="addStop()"
        >
          Add
        </button>
      </div>

      @if (stops().length > 0) {
        <table class="w-full text-left text-sm">
          <thead class="border-b text-xs uppercase text-gray-500">
            <tr>
              <th class="px-3 py-1">#</th>
              <th class="px-3 py-1">Platform</th>
              <th class="px-3 py-1">Dwell (s)</th>
              <th class="px-3 py-1"></th>
            </tr>
          </thead>
          <tbody>
            @for (stop of stops(); track $index; let i = $index) {
              <tr class="border-b">
                <td class="px-3 py-1">{{ i + 1 }}</td>
                <td class="px-3 py-1">{{ stop.platformName }}</td>
                <td class="px-3 py-1">
                  <input
                    type="number"
                    class="w-16 rounded border px-1 py-0.5 text-sm"
                    [ngModel]="stop.dwellTime"
                    (ngModelChange)="updateDwellTime(i, $event)"
                    min="0"
                  />
                </td>
                <td class="px-3 py-1">
                  <button class="text-xs text-red-600 hover:text-red-800" (click)="removeStop(i)">
                    Remove
                  </button>
                </td>
              </tr>
            }
          </tbody>
        </table>
      }
    </div>

    <!-- Start time -->
    <div class="mb-4">
      <label class="mb-1 block text-sm font-medium text-gray-600" for="start-time">
        Start Time
      </label>
      <input
        id="start-time"
        type="datetime-local"
        class="rounded border px-2 py-1 text-sm"
        [(ngModel)]="startTimeLocal"
      />
    </div>

    <!-- Submit -->
    <button
      class="rounded bg-green-600 px-4 py-2 text-sm text-white hover:bg-green-700 disabled:opacity-50"
      [disabled]="stops().length < 2 || !startTimeLocal()"
      (click)="onSubmit()"
    >
      Update Route
    </button>

    <!-- Timetable display -->
    @if (service().timetable.length > 0) {
      <div class="mt-6">
        <h4 class="mb-2 text-sm font-medium text-gray-600">Timetable</h4>
        <table class="w-full text-left text-sm">
          <thead class="border-b text-xs uppercase text-gray-500">
            <tr>
              <th class="px-3 py-1">Node</th>
              <th class="px-3 py-1">Arrival</th>
              <th class="px-3 py-1">Departure</th>
            </tr>
          </thead>
          <tbody>
            @for (entry of service().timetable; track entry.order) {
              <tr class="border-b">
                <td class="px-3 py-1">{{ nodeName(entry.node_id) }}</td>
                <td class="px-3 py-1">{{ formatTime(entry.arrival) }}</td>
                <td class="px-3 py-1">{{ formatTime(entry.departure) }}</td>
              </tr>
            }
          </tbody>
        </table>
      </div>
    }
  `,
})
export class RouteEditorComponent {
  readonly service = input.required<ServiceResponse>();
  readonly graph = input.required<GraphResponse>();
  readonly submitted = output<{
    stops: { platform_id: string; dwell_time: number }[];
    start_time: number;
  }>();
  readonly back = output<void>();

  readonly stops = signal<readonly StopEntry[]>([]);
  readonly selectedPlatformId = signal('');
  readonly startTimeLocal = signal('');

  readonly nonYardStations = computed<readonly Station[]>(() =>
    this.graph().stations.filter((s) => !s.is_yard),
  );

  platformName(platformId: string): string {
    return this.graph().nodes.find((n) => n.id === platformId)?.name ?? platformId;
  }

  nodeName(nodeId: string): string {
    return this.graph().nodes.find((n) => n.id === nodeId)?.name ?? nodeId;
  }

  addStop(): void {
    const pid = this.selectedPlatformId();
    if (!pid) return;
    const name = this.platformName(pid);
    this.stops.update((s) => [...s, { platformId: pid, platformName: name, dwellTime: 30 }]);
    this.selectedPlatformId.set('');
  }

  removeStop(index: number): void {
    this.stops.update((s) => s.filter((_, i) => i !== index));
  }

  updateDwellTime(index: number, value: number): void {
    this.stops.update((s) =>
      s.map((stop, i) => (i === index ? { ...stop, dwellTime: value } : stop)),
    );
  }

  onSubmit(): void {
    const startEpoch = Math.floor(new Date(this.startTimeLocal()).getTime() / 1000);
    this.submitted.emit({
      stops: this.stops().map((s) => ({ platform_id: s.platformId, dwell_time: s.dwellTime })),
      start_time: startEpoch,
    });
  }

  formatTime(epoch: number): string {
    return new Date(epoch * 1000).toLocaleTimeString();
  }
}
