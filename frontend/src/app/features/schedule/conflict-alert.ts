import { Component, computed, input, output } from '@angular/core';
import { ConflictResponse, GraphResponse } from '../../shared/models';
import { EpochTimePipe } from '../../shared/pipes/epoch-time.pipe';

@Component({
  selector: 'app-conflict-alert',
  imports: [EpochTimePipe],
  template: `
    <div class="relative mb-4 rounded border border-red-300 bg-red-50 p-4 text-sm">
      <button
        class="absolute right-2 top-2 text-red-400 hover:text-red-600"
        (click)="dismiss.emit()"
      >
        &times;
      </button>
      <h4 class="mb-2 font-semibold text-red-800">Conflicts Detected</h4>

      @if (conflicts().vehicle_conflicts.length > 0) {
        <div class="mb-2">
          <h5 class="font-medium text-red-700">Vehicle Conflicts</h5>
          <ul class="ml-4 list-disc">
            @for (c of conflicts().vehicle_conflicts; track $index) {
              <li>
                {{ vehicleName(c.vehicle_id) }} — S{{ c.service_a_id }} &amp; S{{ c.service_b_id }}:
                {{ c.reason }}
              </li>
            }
          </ul>
        </div>
      }

      @if (conflicts().block_conflicts.length > 0) {
        <div class="mb-2">
          <h5 class="font-medium text-red-700">Block Conflicts</h5>
          <ul class="ml-4 list-disc">
            @for (c of conflicts().block_conflicts; track $index) {
              <li>
                {{ nodeName(c.block_id) }} — S{{ c.service_a_id }} &amp; S{{ c.service_b_id }} ({{
                  c.overlap_start | epochTime
                }}
                – {{ c.overlap_end | epochTime }})
              </li>
            }
          </ul>
        </div>
      }

      @if (conflicts().interlocking_conflicts.length > 0) {
        <div class="mb-2">
          <h5 class="font-medium text-red-700">Interlocking Conflicts</h5>
          <ul class="ml-4 list-disc">
            @for (c of conflicts().interlocking_conflicts; track $index) {
              <li>
                Group {{ c.group }} — {{ nodeName(c.block_a_id) }} &amp;
                {{ nodeName(c.block_b_id) }}, S{{ c.service_a_id }} &amp; S{{ c.service_b_id }} ({{
                  c.overlap_start | epochTime
                }}
                – {{ c.overlap_end | epochTime }})
              </li>
            }
          </ul>
        </div>
      }

      @for (c of conflicts().battery_conflicts; track $index) {
        @if (c.type === 'low_battery') {
          <div class="mb-2">
            <h5 class="font-medium text-red-700">Low Battery</h5>
            <ul class="ml-4 list-disc">
              <li>S{{ c.service_id }} has insufficient battery to complete the route</li>
            </ul>
          </div>
        } @else if (c.type === 'insufficient_charge') {
          <div class="mb-2">
            <h5 class="font-medium text-red-700">Insufficient Charge</h5>
            <ul class="ml-4 list-disc">
              <li>S{{ c.service_id }} — insufficient charging time between services</li>
            </ul>
          </div>
        }
      }
    </div>
  `,
})
export class ConflictAlertComponent {
  readonly conflicts = input.required<ConflictResponse>();
  readonly graph = input.required<GraphResponse>();
  readonly dismiss = output<void>();

  private readonly nodeNameMap = computed(() => {
    const map = new Map<string, string>();
    for (const node of this.graph().nodes) {
      map.set(node.id, node.name);
    }
    return map;
  });

  private readonly vehicleNameMap = computed(() => {
    const map = new Map<string, string>();
    for (const v of this.graph().vehicles) {
      map.set(v.id, v.name);
    }
    return map;
  });

  nodeName(id: string): string {
    return this.nodeNameMap().get(id) ?? id;
  }

  vehicleName(id: string): string {
    return this.vehicleNameMap().get(id) ?? id;
  }
}
