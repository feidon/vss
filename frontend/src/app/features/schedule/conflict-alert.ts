import { Component, computed, input, output } from '@angular/core';
import { ConflictResponse, GraphResponse } from '../../shared/models';
import { EpochTimePipe } from '../../shared/pipes/epoch-time.pipe';

@Component({
  selector: 'app-conflict-alert',
  imports: [EpochTimePipe],
  template: `
    <div
      class="animate-fade-in relative mb-4 overflow-hidden rounded-lg border border-signal-danger/25 bg-signal-danger/5 p-5 text-sm shadow-[0_0_24px_var(--color-glow-red)]"
    >
      <!-- Animated scan line -->
      <div class="pointer-events-none absolute inset-x-0 top-0 h-px overflow-hidden">
        <div
          class="h-full w-1/3 bg-gradient-to-r from-transparent via-signal-danger/60 to-transparent"
          style="animation: scan-line 3s linear infinite"
        ></div>
      </div>

      <button
        class="absolute right-3 top-3 rounded-md p-1 text-signal-danger/50 transition-colors hover:bg-signal-danger/10 hover:text-signal-danger"
        (click)="dismiss.emit()"
      >
        <svg class="h-4 w-4" viewBox="0 0 16 16" fill="currentColor">
          <path
            d="M3.72 3.72a.75.75 0 011.06 0L8 6.94l3.22-3.22a.75.75 0 111.06 1.06L9.06 8l3.22 3.22a.75.75 0 11-1.06 1.06L8 9.06l-3.22 3.22a.75.75 0 01-1.06-1.06L6.94 8 3.72 4.78a.75.75 0 010-1.06z"
          />
        </svg>
      </button>

      <div class="mb-3 flex items-center gap-2">
        <svg class="h-5 w-5 text-signal-danger" viewBox="0 0 20 20" fill="currentColor">
          <path
            fill-rule="evenodd"
            d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.168 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z"
            clip-rule="evenodd"
          />
        </svg>
        <h4 class="font-display text-base font-bold text-signal-danger">Conflicts Detected</h4>
      </div>

      <div class="space-y-3 pl-7">
        @if (conflicts().vehicle_conflicts.length > 0) {
          <div>
            <h5
              class="mb-1 font-display text-xs font-semibold uppercase tracking-wider text-signal-danger/80"
            >
              Vehicle Conflicts
            </h5>
            <ul class="space-y-0.5">
              @for (c of conflicts().vehicle_conflicts; track $index) {
                <li class="flex items-start gap-2 text-signal-danger/70">
                  <span class="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-signal-danger/50"></span>
                  <span class="font-display">
                    {{ vehicleName(c.vehicle_id) }} — S{{ c.service_a_id }} &amp; S{{
                      c.service_b_id
                    }}:
                    {{ c.reason }}
                  </span>
                </li>
              }
            </ul>
          </div>
        }

        @if (conflicts().block_conflicts.length > 0) {
          <div>
            <h5
              class="mb-1 font-display text-xs font-semibold uppercase tracking-wider text-signal-danger/80"
            >
              Block Conflicts
            </h5>
            <ul class="space-y-0.5">
              @for (c of conflicts().block_conflicts; track $index) {
                <li class="flex items-start gap-2 text-signal-danger/70">
                  <span class="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-signal-danger/50"></span>
                  <span class="font-display">
                    {{ nodeName(c.block_id) }} — S{{ c.service_a_id }} &amp; S{{ c.service_b_id }}
                    <span class="font-mono text-xs"
                      >({{ c.overlap_start | epochTime }} – {{ c.overlap_end | epochTime }})</span
                    >
                  </span>
                </li>
              }
            </ul>
          </div>
        }

        @if (conflicts().interlocking_conflicts.length > 0) {
          <div>
            <h5
              class="mb-1 font-display text-xs font-semibold uppercase tracking-wider text-signal-danger/80"
            >
              Interlocking Conflicts
            </h5>
            <ul class="space-y-0.5">
              @for (c of conflicts().interlocking_conflicts; track $index) {
                <li class="flex items-start gap-2 text-signal-danger/70">
                  <span class="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-signal-danger/50"></span>
                  <span class="font-display">
                    Group {{ c.group }} — {{ nodeName(c.block_a_id) }} &amp;
                    {{ nodeName(c.block_b_id) }}, S{{ c.service_a_id }} &amp; S{{ c.service_b_id }}
                    <span class="font-mono text-xs"
                      >({{ c.overlap_start | epochTime }} – {{ c.overlap_end | epochTime }})</span
                    >
                  </span>
                </li>
              }
            </ul>
          </div>
        }

        @for (c of conflicts().battery_conflicts; track $index) {
          <div>
            <h5
              class="mb-1 font-display text-xs font-semibold uppercase tracking-wider text-signal-caution"
            >
              {{ c.type === 'low_battery' ? 'Low Battery' : 'Insufficient Charge' }}
            </h5>
            <ul>
              <li class="flex items-start gap-2 text-signal-caution/70">
                <span class="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-signal-caution/50"></span>
                <span class="font-display">
                  S{{ c.service_id }} —
                  {{
                    c.type === 'low_battery'
                      ? 'insufficient battery to complete the route'
                      : 'insufficient charging time between services'
                  }}
                </span>
              </li>
            </ul>
          </div>
        }
      </div>
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
    for (const edge of this.graph().edges) {
      map.set(edge.id, edge.name);
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
