import { Component, input, output } from '@angular/core';
import { ServiceResponse, Node } from '../../shared/models';
import { EpochTimePipe } from '../../shared/pipes/epoch-time.pipe';

@Component({
  selector: 'app-timetable-detail',
  imports: [EpochTimePipe],
  template: `
    <div class="mb-4 flex items-center gap-4">
      <button
        class="rounded bg-gray-200 px-3 py-1.5 text-sm hover:bg-gray-300"
        (click)="back.emit()"
      >
        &larr; Back to list
      </button>
      <div>
        <h3 class="text-lg font-semibold">{{ service().name }}</h3>
        <p class="text-sm text-gray-500">Vehicle: {{ vehicleName() }}</p>
      </div>
    </div>

    @if (service().timetable.length === 0) {
      <p class="py-4 text-gray-500">No timetable — route not yet configured.</p>
    } @else {
      <table class="w-full text-left text-sm">
        <thead class="border-b text-xs uppercase text-gray-500">
          <tr>
            <th class="px-3 py-2">#</th>
            <th class="px-3 py-2">Node</th>
            <th class="px-3 py-2">Type</th>
            <th class="px-3 py-2">Arrival</th>
            <th class="px-3 py-2">Departure</th>
          </tr>
        </thead>
        <tbody>
          @for (entry of sortedEntries(); track entry.order) {
            <tr
              class="border-b"
              [class.bg-blue-50]="nodeType(entry.node_id) === 'platform'"
              [class.font-semibold]="nodeType(entry.node_id) === 'platform'"
            >
              <td class="px-3 py-2">{{ entry.order + 1 }}</td>
              <td class="px-3 py-2">{{ nodeName(entry.node_id) }}</td>
              <td class="px-3 py-2 capitalize">{{ nodeType(entry.node_id) }}</td>
              <td class="px-3 py-2">{{ entry.arrival | epochTime }}</td>
              <td class="px-3 py-2">{{ entry.departure | epochTime }}</td>
            </tr>
          }
        </tbody>
      </table>
    }
  `,
})
export class TimetableDetailComponent {
  readonly service = input.required<ServiceResponse>();
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
    return this.service().path.find((n) => n.id === nodeId);
  }
}
