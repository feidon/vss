import { Component, input, output } from '@angular/core';
import { ConflictResponse } from '../../shared/models';

@Component({
  selector: 'app-conflict-alert',
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
              <li>Services {{ c.service_a_id }} &amp; {{ c.service_b_id }}: {{ c.reason }}</li>
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
                Block {{ c.block_id }} — Services {{ c.service_a_id }} &amp;
                {{ c.service_b_id }} ({{ formatTime(c.overlap_start) }} –
                {{ formatTime(c.overlap_end) }})
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
                Group {{ c.group }} — Blocks {{ c.block_a_id }} &amp; {{ c.block_b_id }}, Services
                {{ c.service_a_id }} &amp; {{ c.service_b_id }} ({{ formatTime(c.overlap_start) }} –
                {{ formatTime(c.overlap_end) }})
              </li>
            }
          </ul>
        </div>
      }

      @if (conflicts().low_battery_conflicts.length > 0) {
        <div class="mb-2">
          <h5 class="font-medium text-red-700">Low Battery</h5>
          <ul class="ml-4 list-disc">
            @for (c of conflicts().low_battery_conflicts; track $index) {
              <li>Service {{ c.service_id }} has insufficient battery to complete the route</li>
            }
          </ul>
        </div>
      }

      @if (conflicts().insufficient_charge_conflicts.length > 0) {
        <div class="mb-2">
          <h5 class="font-medium text-red-700">Insufficient Charge</h5>
          <ul class="ml-4 list-disc">
            @for (c of conflicts().insufficient_charge_conflicts; track $index) {
              <li>
                Services {{ c.service_a_id }} &amp; {{ c.service_b_id }} — insufficient charging
                time between services
              </li>
            }
          </ul>
        </div>
      }
    </div>
  `,
})
export class ConflictAlertComponent {
  readonly conflicts = input.required<ConflictResponse>();
  readonly dismiss = output<void>();

  formatTime(epoch: number): string {
    return new Date(epoch * 1000).toLocaleTimeString();
  }
}
