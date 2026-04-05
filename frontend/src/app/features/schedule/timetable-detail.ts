import { Component, input, output } from '@angular/core';
import { ServiceDetailResponse, Node } from '../../shared/models';
import { EpochTimePipe } from '../../shared/pipes/epoch-time.pipe';

@Component({
  selector: 'app-timetable-detail',
  imports: [EpochTimePipe],
  template: `
    <div class="mb-6 flex items-center gap-4 animate-fade-in">
      <button
        class="rounded-lg border border-edge px-3 py-2 font-display text-base text-ink-secondary transition-colors hover:bg-panel-hover hover:text-ink"
        (click)="back.emit()"
      >
        &larr; Back
      </button>
      <div>
        <h3 class="font-display text-xl font-bold text-ink">{{ service().name }}</h3>
        <p class="font-display text-base text-ink-muted">Vehicle: {{ vehicleName() }}</p>
      </div>
    </div>

    @if (service().timetable.length === 0) {
      <p class="py-8 text-center font-display text-base text-ink-muted">
        No timetable — route not yet configured.
      </p>
    } @else {
      <div class="card overflow-hidden animate-fade-in delay-1">
        <table class="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Node</th>
              <th>Type</th>
              <th>Arrival</th>
              <th>Departure</th>
            </tr>
          </thead>
          <tbody>
            @for (entry of sortedEntries(); track entry.order) {
              <tr [class.!bg-signal-info/5]="nodeType(entry.node_id) === 'platform'">
                <td class="font-mono text-sm text-ink-muted">{{ entry.order + 1 }}</td>
                <td class="font-display font-semibold text-ink">{{ nodeName(entry.node_id) }}</td>
                <td>
                  <span
                    class="inline-flex rounded-md px-2 py-0.5 text-sm capitalize"
                    [class]="
                      nodeType(entry.node_id) === 'platform'
                        ? 'bg-signal-info/10 text-signal-info ring-1 ring-signal-info/20'
                        : nodeType(entry.node_id) === 'yard'
                          ? 'bg-signal-caution/10 text-signal-caution ring-1 ring-signal-caution/20'
                          : 'bg-panel-raised text-ink-muted ring-1 ring-edge'
                    "
                    >{{ nodeType(entry.node_id) }}</span
                  >
                </td>
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
export class TimetableDetailComponent {
  readonly service = input.required<ServiceDetailResponse>();
  readonly vehicleName = input.required<string>();
  readonly back = output<void>();

  sortedEntries(): readonly import('../../shared/models').TimetableEntry[] {
    return [...this.service().timetable].sort((a, b) => a.order - b.order);
  }

  nodeName(nodeId: string): string {
    return this.findNode(nodeId)?.name ?? nodeId;
  }

  nodeType(nodeId: string): string {
    return this.findNode(nodeId)?.type ?? 'unknown';
  }

  private findNode(nodeId: string): Node | undefined {
    return this.service().route.find((n) => n.id === nodeId);
  }
}
