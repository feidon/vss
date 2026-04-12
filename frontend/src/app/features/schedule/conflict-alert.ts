import { Component, computed, input, output } from '@angular/core';
import {
  ConflictResponse,
  GraphResponse,
  VehicleConflict,
  BlockConflict,
  InterlockingConflict,
} from '../../shared/models';
import { EpochTimePipe } from '../../shared/pipes/epoch-time.pipe';

const epochPipe = new EpochTimePipe();

interface ConflictSection {
  readonly title: string;
  readonly items: readonly string[];
}

@Component({
  selector: 'app-conflict-alert',
  imports: [],
  template: `
    <div
      class="animate-fade-in relative mb-4 overflow-hidden rounded-lg border border-signal-danger/25 bg-signal-danger/5 p-5 text-base shadow-[0_0_24px_var(--color-glow-red)]"
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
        @for (section of conflictSections(); track section.title) {
          <div>
            <h5
              class="mb-1 font-display text-sm font-semibold uppercase tracking-wider text-signal-danger/80"
            >
              {{ section.title }}
            </h5>
            <ul class="space-y-0.5">
              @for (item of section.items; track $index) {
                <li class="flex items-start gap-2 text-signal-danger/70">
                  <span class="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-signal-danger/50"></span>
                  <span class="font-display">{{ item }}</span>
                </li>
              }
            </ul>
          </div>
        }

        @for (c of conflicts().battery_conflicts; track $index) {
          <div>
            <h5
              class="mb-1 font-display text-sm font-semibold uppercase tracking-wider text-signal-caution"
            >
              {{ c.type === 'low_battery' ? 'Low Battery' : 'Insufficient Charge' }}
            </h5>
            <ul>
              <li class="flex items-start gap-2 text-signal-caution/70">
                <span class="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-signal-caution/50"></span>
                <span class="font-display">
                  {{ c.service_name }} -
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

  readonly conflictSections = computed<readonly ConflictSection[]>(() => {
    const c = this.conflicts();
    const sections: ConflictSection[] = [];

    if (c.vehicle_conflicts.length > 0) {
      sections.push({
        title: 'Vehicle Conflicts',
        items: c.vehicle_conflicts.map(
          (v: VehicleConflict) =>
            `${this.vehicleName(v.vehicle_id)} - ${v.service_a_name} & ${v.service_b_name}: ${v.reason}`,
        ),
      });
    }

    if (c.block_conflicts.length > 0) {
      sections.push({
        title: 'Block Conflicts',
        items: c.block_conflicts.map(
          (b: BlockConflict) =>
            `${this.nodeName(b.block_id)} - ${b.service_a_name} & ${b.service_b_name} (${epochPipe.transform(b.overlap_start)} – ${epochPipe.transform(b.overlap_end)})`,
        ),
      });
    }

    if (c.interlocking_conflicts.length > 0) {
      sections.push({
        title: 'Interlocking Conflicts',
        items: c.interlocking_conflicts.map(
          (ic: InterlockingConflict) =>
            `Group ${ic.group} - ${this.nodeName(ic.block_a_id)} & ${this.nodeName(ic.block_b_id)}, ${ic.service_a_name} & ${ic.service_b_name} (${epochPipe.transform(ic.overlap_start)} – ${epochPipe.transform(ic.overlap_end)})`,
        ),
      });
    }

    return sections;
  });

  nodeName(id: string): string {
    return this.nodeNameMap().get(id) ?? id;
  }

  vehicleName(id: string): string {
    return this.vehicleNameMap().get(id) ?? id;
  }
}
