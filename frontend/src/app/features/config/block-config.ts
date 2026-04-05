import {
  afterNextRender,
  Component,
  computed,
  ElementRef,
  inject,
  Injector,
  OnInit,
  signal,
  viewChild,
} from '@angular/core';
import { BlockService } from '../../core/services/block.service';
import { BlockResponse } from '../../shared/models';
import { ErrorAlertComponent } from '../../shared/components/error-alert';

interface BlockGroup {
  readonly group: number;
  readonly blocks: readonly BlockResponse[];
}

@Component({
  selector: 'app-block-config',
  imports: [ErrorAlertComponent],
  template: `
    <div class="mb-6 animate-fade-in">
      <h2 class="font-display text-2xl font-bold tracking-wide text-ink">Block Configuration</h2>
      <p class="mt-0.5 font-display text-sm text-ink-muted">Track section traversal times</p>
    </div>

    @if (error()) {
      <app-error-alert [message]="error()!" (dismiss)="error.set(null)" />
    }

    <div class="card overflow-hidden animate-fade-in delay-1">
      <table class="data-table">
        <thead>
          <tr>
            <th>Block</th>
            <th>Group</th>
            <th>Traversal Time</th>
          </tr>
        </thead>
        @for (g of groupedBlocks(); track g.group) {
          <tbody>
            <tr data-testid="group-header">
              <td colspan="3" class="!border-b-edge bg-panel-raised px-4 py-2">
                <div class="flex items-center gap-2">
                  <span
                    class="h-1.5 w-1.5 rounded-full"
                    [class]="g.group === 0 ? 'bg-ink-muted' : 'bg-signal-caution'"
                  ></span>
                  <span
                    class="font-display text-xs font-semibold uppercase tracking-wider text-ink-muted"
                  >
                    {{ g.group === 0 ? 'Ungrouped' : 'Interlocking Group ' + g.group }}
                  </span>
                </div>
              </td>
            </tr>
            @for (block of g.blocks; track block.id) {
              <tr class="h-10 transition-colors">
                <td class="font-display font-semibold text-ink">{{ block.name }}</td>
                <td>
                  @if (block.group !== 0) {
                    <span
                      class="inline-flex items-center rounded-md bg-signal-caution/10 px-2 py-0.5 font-mono text-xs font-medium text-signal-caution ring-1 ring-signal-caution/20"
                    >
                      {{ block.group }}
                    </span>
                  } @else {
                    <span class="text-ink-muted">—</span>
                  }
                </td>
                <td>
                  <div class="flex items-center gap-2">
                    @if (editingBlockId() === block.id) {
                      <input
                        #editInput
                        type="number"
                        class="h-7 w-20 rounded-md px-2 font-mono text-sm"
                        [value]="editValue()"
                        (input)="onEditInput($event)"
                        (keydown)="onKeydown($event, block)"
                        (blur)="onBlur(block)"
                      />
                      @if (validationError()) {
                        <span class="font-display text-xs text-signal-danger">{{
                          validationError()
                        }}</span>
                      }
                    } @else {
                      <span
                        class="cursor-pointer rounded-md px-2 py-0.5 font-mono text-sm text-signal-info transition-colors hover:bg-signal-info/10"
                        tabindex="0"
                        role="button"
                        (click)="startEdit(block)"
                        (keydown.enter)="startEdit(block)"
                        (keydown.space)="startEdit(block)"
                        >{{ block.traversal_time_seconds }}s</span
                      >
                    }
                    <button
                      type="button"
                      aria-label="Edit traversal time"
                      (mousedown)="toggleEdit($event, block)"
                      class="shrink-0 cursor-pointer rounded-md p-1 text-ink-muted transition-colors hover:bg-signal-info/10 hover:text-signal-info"
                    >
                      <svg
                        class="h-3.5 w-3.5"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                        aria-hidden="true"
                      >
                        <path
                          d="M2.695 14.763l-1.262 3.154a.5.5 0 00.65.65l3.155-1.262a4 4 0 001.343-.885L17.5 5.5a2.121 2.121 0 00-3-3L3.58 13.42a4 4 0 00-.885 1.343z"
                        />
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
            }
          </tbody>
        }
      </table>
    </div>
  `,
})
export class BlockConfigComponent implements OnInit {
  private readonly blockService = inject(BlockService);
  private readonly injector = inject(Injector);

  private readonly editInput = viewChild<ElementRef<HTMLInputElement>>('editInput');

  readonly blocks = signal<readonly BlockResponse[]>([]);
  readonly error = signal<string | null>(null);
  readonly editingBlockId = signal<string | null>(null);
  readonly editValue = signal(0);
  readonly validationError = signal<string | null>(null);

  readonly groupedBlocks = computed<readonly BlockGroup[]>(() => {
    const byGroup = new Map<number, BlockResponse[]>();
    for (const block of this.blocks()) {
      const list = byGroup.get(block.group) ?? [];
      list.push(block);
      byGroup.set(block.group, list);
    }
    return Array.from(byGroup.entries())
      .sort(([a], [b]) => a - b)
      .map(([group, blocks]) => ({
        group,
        blocks: [...blocks].sort((a, b) =>
          a.name.localeCompare(b.name, undefined, { numeric: true }),
        ),
      }));
  });

  ngOnInit(): void {
    this.blockService.getBlocks().subscribe({
      next: (blocks) => {
        blocks.sort((a, b) => a.id.localeCompare(b.id));
        this.blocks.set(blocks);
      },
      error: () => this.error.set('Failed to load blocks.'),
    });
  }

  toggleEdit(event: MouseEvent, block: BlockResponse): void {
    event.preventDefault();
    if (this.editingBlockId() === block.id) {
      this.save(block);
    } else {
      this.startEdit(block);
    }
  }

  startEdit(block: BlockResponse): void {
    this.editingBlockId.set(block.id);
    this.editValue.set(block.traversal_time_seconds);
    this.validationError.set(null);
    afterNextRender(
      () => {
        this.editInput()?.nativeElement.focus();
      },
      { injector: this.injector },
    );
  }

  onEditInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.editValue.set(input.valueAsNumber);
  }

  onKeydown(event: KeyboardEvent, block: BlockResponse): void {
    if (event.key === 'Enter') {
      this.save(block);
    } else if (event.key === 'Escape') {
      this.cancelEdit();
    }
  }

  onBlur(block: BlockResponse): void {
    this.save(block);
  }

  private save(block: BlockResponse): void {
    const value = this.editValue();
    if (!Number.isInteger(value) || value < 1) {
      this.validationError.set('Must be a positive integer (≥ 1).');
      return;
    }
    this.validationError.set(null);
    const previousValue = block.traversal_time_seconds;
    this.updateBlockLocally(block.id, value);
    this.editingBlockId.set(null);
    this.blockService.updateBlock(block.id, { traversal_time_seconds: value }).subscribe({
      error: () => {
        this.updateBlockLocally(block.id, previousValue);
        this.error.set(`Failed to update ${block.name}.`);
      },
    });
  }

  private cancelEdit(): void {
    this.editingBlockId.set(null);
    this.validationError.set(null);
  }

  private updateBlockLocally(id: string, traversalTime: number): void {
    this.blocks.update((blocks) =>
      blocks.map((b) => (b.id === id ? { ...b, traversal_time_seconds: traversalTime } : b)),
    );
  }
}
