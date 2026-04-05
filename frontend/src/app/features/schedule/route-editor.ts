import { Component, effect, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ServiceDetailResponse, GraphResponse, TimetableEntry } from '../../shared/models';
import { EpochTimePipe } from '../../shared/pipes/epoch-time.pipe';
import { localDatetimeToEpoch, epochToLocalDatetime } from '../../shared/utils/time-utils';

interface StopEntry {
  readonly nodeId: string;
  readonly nodeName: string;
  readonly dwellTime: number;
}

@Component({
  selector: 'app-route-editor',
  imports: [FormsModule, EpochTimePipe],
  template: `
    <!-- Stop list -->
    <div class="mb-5">
      <h4 class="mb-2 font-display text-sm font-semibold uppercase tracking-wider text-ink-muted">
        Stops
      </h4>

      @if (stops().length > 0) {
        <div class="space-y-1">
          @for (stop of stops(); track $index; let i = $index) {
            <div
              class="flex items-center gap-3 rounded-lg bg-panel-raised/60 px-3 py-2 ring-1 ring-edge/50 transition-colors hover:ring-edge-bright/50"
            >
              <span
                class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-signal-info/15 font-mono text-sm font-medium text-signal-info"
              >
                {{ i + 1 }}
              </span>
              <span class="flex-1 font-display text-base font-medium text-ink">
                {{ stop.nodeName }}
              </span>
              <div class="flex items-center gap-1.5">
                <input
                  type="number"
                  class="h-7 w-16 rounded-md px-2 text-center font-mono text-sm"
                  [ngModel]="stop.dwellTime"
                  (ngModelChange)="updateDwellTime(i, $event)"
                  min="0"
                />
                <span class="text-xs text-ink-muted">s</span>
              </div>
              <button
                class="rounded-md p-1 text-ink-muted transition-colors hover:bg-signal-danger/10 hover:text-signal-danger"
                title="Remove stop"
                (click)="removeStop(i)"
              >
                <svg class="h-3.5 w-3.5" viewBox="0 0 16 16" fill="currentColor">
                  <path
                    d="M3.72 3.72a.75.75 0 011.06 0L8 6.94l3.22-3.22a.75.75 0 111.06 1.06L9.06 8l3.22 3.22a.75.75 0 11-1.06 1.06L8 9.06l-3.22 3.22a.75.75 0 01-1.06-1.06L6.94 8 3.72 4.78a.75.75 0 010-1.06z"
                  />
                </svg>
              </button>
            </div>
          }
        </div>
      } @else {
        <p
          class="rounded-lg border border-dashed border-edge py-6 text-center font-display text-sm text-ink-muted"
        >
          Click stops on the track map to add them
        </p>
      }
    </div>

    <!-- Start time -->
    <div class="mb-5">
      <label
        class="mb-1.5 block font-display text-sm font-semibold uppercase tracking-wider text-ink-muted"
        for="start-time"
      >
        Start Time
      </label>
      <input
        id="start-time"
        type="datetime-local"
        class="h-9 w-full rounded-lg px-3 font-mono text-base"
        [(ngModel)]="startTimeLocal"
      />
    </div>

    <!-- Submit -->
    <button
      class="w-full rounded-lg bg-signal-clear/15 px-4 py-2.5 font-display text-base font-semibold text-signal-clear ring-1 ring-signal-clear/25 transition-all hover:bg-signal-clear/25 hover:ring-signal-clear/40 hover:shadow-[0_0_16px_var(--color-glow-green)] disabled:opacity-30 disabled:hover:bg-signal-clear/15 disabled:hover:shadow-none"
      [disabled]="stops().length < 2 || !startTimeLocal()"
      (click)="onSubmit()"
    >
      Update Route
    </button>

    <!-- Timetable display -->
    @if (service().timetable.length > 0) {
      <div class="mt-6 border-t border-edge pt-5">
        <h4 class="mb-3 font-display text-sm font-semibold uppercase tracking-wider text-ink-muted">
          Timetable
        </h4>
        <table class="data-table">
          <thead>
            <tr>
              <th>Node</th>
              <th>Arrival</th>
              <th>Departure</th>
            </tr>
          </thead>
          <tbody>
            @for (entry of service().timetable; track entry.order) {
              <tr>
                <td class="font-display font-medium text-ink">{{ nodeName(entry.node_id) }}</td>
                <td class="font-mono text-sm text-signal-info">{{ entry.arrival | epochTime }}</td>
                <td class="font-mono text-sm text-signal-info">
                  {{ entry.departure | epochTime }}
                </td>
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
  readonly stopsChanged = output<readonly string[]>();

  readonly stops = signal<readonly StopEntry[]>([]);
  readonly startTimeLocal = signal('');

  constructor() {
    effect(() => {
      this.deriveInitialState(this.service());
    });
    effect(() => {
      const ids = this.stops().map((s) => s.nodeId);
      this.stopsChanged.emit(ids);
    });
  }

  addStopFromMap(nodeId: string, nodeName: string): void {
    this.stops.update((s) => [...s, { nodeId, nodeName, dwellTime: 30 }]);
  }

  nodeName(nodeId: string): string {
    return (
      this.service().route.find((n) => n.id === nodeId)?.name ??
      this.graph().edges.find((e) => e.id === nodeId)?.name ??
      nodeId
    );
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
    this.submitted.emit({
      stops: this.stops().map((s) => ({ node_id: s.nodeId, dwell_time: s.dwellTime })),
      start_time: localDatetimeToEpoch(this.startTimeLocal()),
    });
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
      this.startTimeLocal.set(epochToLocalDatetime(sorted[0].arrival));
    }
  }
}
