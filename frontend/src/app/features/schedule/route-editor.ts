import { Component, computed, effect, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ServiceDetailResponse, GraphResponse, Station, TimetableEntry } from '../../shared/models';

interface StopEntry {
  readonly nodeId: string;
  readonly nodeName: string;
  readonly dwellTime: number;
}

@Component({
  selector: 'app-route-editor',
  imports: [FormsModule],
  template: `
    <!-- Stop picker -->
    <div class="mb-4">
      <h4 class="mb-2 text-sm font-medium text-gray-600">Stops</h4>
      <div class="mb-2 flex items-center gap-2">
        <select class="rounded border px-2 py-1 text-sm" [(ngModel)]="selectedNodeId">
          <option value="">Add a stop...</option>
          @for (station of stations(); track station.id) {
            @if (station.is_yard) {
              <option [value]="yardNodeId(station)">{{ station.name }} (Yard)</option>
            } @else {
              <optgroup [label]="station.name">
                @for (pid of station.platform_ids; track pid) {
                  <option [value]="pid">{{ nodeName(pid) }}</option>
                }
              </optgroup>
            }
          }
        </select>
        <button
          class="rounded bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-700 disabled:opacity-50"
          [disabled]="!selectedNodeId()"
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
              <th class="px-3 py-1">Stop</th>
              <th class="px-3 py-1">Dwell (s)</th>
              <th class="px-3 py-1"></th>
            </tr>
          </thead>
          <tbody>
            @for (stop of stops(); track $index; let i = $index) {
              <tr class="border-b">
                <td class="px-3 py-1">{{ i + 1 }}</td>
                <td class="px-3 py-1">{{ stop.nodeName }}</td>
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
  readonly service = input.required<ServiceDetailResponse>();
  readonly graph = input.required<GraphResponse>();
  readonly submitted = output<{
    stops: { node_id: string; dwell_time: number }[];
    start_time: number;
  }>();
  readonly back = output<void>();
  readonly stopsChanged = output<readonly string[]>();

  readonly stops = signal<readonly StopEntry[]>([]);
  readonly selectedNodeId = signal('');
  readonly startTimeLocal = signal('');

  readonly stations = computed<readonly Station[]>(() => this.graph().stations);

  private initialized = false;

  constructor() {
    effect(() => {
      const svc = this.service();
      const graph = this.graph();
      if (this.initialized || !svc || !graph) return;
      this.initialized = true;
      this.deriveInitialState(svc);
    });

    effect(() => {
      const ids = this.stops().map((s) => s.nodeId);
      this.stopsChanged.emit(ids);
    });
  }

  addStopFromMap(nodeId: string, nodeName: string): void {
    this.stops.update((s) => [...s, { nodeId, nodeName, dwellTime: 30 }]);
  }

  yardNodeId(station: Station): string {
    const yardNode = this.graph().nodes.find((n) => n.type === 'yard' && n.name === station.name);
    return yardNode?.id ?? '';
  }

  nodeName(nodeId: string): string {
    return this.graph().nodes.find((n) => n.id === nodeId)?.name ?? nodeId;
  }

  addStop(): void {
    const nid = this.selectedNodeId();
    if (!nid) return;
    const name = this.nodeName(nid);
    this.stops.update((s) => [...s, { nodeId: nid, nodeName: name, dwellTime: 30 }]);
    this.selectedNodeId.set('');
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
      stops: this.stops().map((s) => ({ node_id: s.nodeId, dwell_time: s.dwellTime })),
      start_time: startEpoch,
    });
  }

  formatTime(epoch: number): string {
    return new Date(epoch * 1000).toLocaleTimeString();
  }

  private deriveInitialState(svc: ServiceDetailResponse): void {
    if (svc.route.length === 0) return;

    const timetableMap = new Map<string, TimetableEntry>();
    for (const entry of svc.timetable) {
      timetableMap.set(entry.node_id, entry);
    }

    const stopNodes = svc.route.filter((n) => n.type !== 'block');
    const initialStops: StopEntry[] = stopNodes.map((node) => {
      const entry = timetableMap.get(node.id);
      const dwellTime = entry ? entry.departure - entry.arrival : 30;
      return { nodeId: node.id, nodeName: node.name, dwellTime };
    });
    this.stops.set(initialStops);

    if (svc.timetable.length > 0) {
      const sorted = [...svc.timetable].sort((a, b) => a.order - b.order);
      const startEpoch = sorted[0].arrival;
      const dt = new Date(startEpoch * 1000);
      const pad = (n: number) => String(n).padStart(2, '0');
      const local = `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())}T${pad(dt.getHours())}:${pad(dt.getMinutes())}`;
      this.startTimeLocal.set(local);
    }
  }
}
