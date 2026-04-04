import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { BlockService } from '../../core/services/block.service';
import { BlockResponse } from '../../shared/models';

interface BlockGroup {
  readonly group: number;
  readonly blocks: readonly BlockResponse[];
}

@Component({
  selector: 'app-block-config',
  template: `
    <h2 class="mb-4 text-xl font-semibold">Block Configuration</h2>

    @if (error()) {
      <p class="mb-4 text-red-600">{{ error() }}</p>
    }

    <table class="w-full border-collapse text-sm">
      <thead>
        <tr class="border-b text-left text-gray-500">
          <th class="px-3 py-2">Block</th>
          <th class="px-3 py-2">Group</th>
          <th class="px-3 py-2">Traversal Time (s)</th>
        </tr>
      </thead>
      @for (g of groupedBlocks(); track g.group) {
        <tbody>
          <tr data-testid="group-header">
            <td colspan="3" class="bg-gray-100 px-3 py-1 text-xs font-semibold text-gray-600">
              {{ g.group === 0 ? 'Ungrouped' : 'Group ' + g.group }}
            </td>
          </tr>
          @for (block of g.blocks; track block.id) {
            <tr class="border-b hover:bg-gray-50">
              <td class="px-3 py-2 font-medium">{{ block.name }}</td>
              <td class="px-3 py-2">{{ block.group }}</td>
              <td class="px-3 py-2">
                @if (editingBlockId() === block.id) {
                  <input
                    type="number"
                    class="w-20 rounded border px-2 py-1"
                    [value]="editValue()"
                    (input)="onEditInput($event)"
                    (keydown)="onKeydown($event, block)"
                    (blur)="onBlur()"
                  />
                  @if (validationError()) {
                    <span class="ml-2 text-xs text-red-500">{{ validationError() }}</span>
                  }
                } @else {
                  <span
                    class="group inline-flex cursor-pointer items-center gap-1 rounded px-1 hover:bg-blue-50"
                    tabindex="0"
                    role="button"
                    (click)="startEdit(block)"
                    (keydown.enter)="startEdit(block)"
                    (keydown.space)="startEdit(block)"
                    >{{ block.traversal_time_seconds
                    }}<svg
                      class="inline h-3.5 w-3.5 text-gray-400 group-hover:text-blue-600"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      aria-hidden="true"
                    >
                      <path
                        d="M2.695 14.763l-1.262 3.154a.5.5 0 00.65.65l3.155-1.262a4 4 0 001.343-.885L17.5 5.5a2.121 2.121 0 00-3-3L3.58 13.42a4 4 0 00-.885 1.343z"
                      /></svg
                  ></span>
                }
              </td>
            </tr>
          }
        </tbody>
      }
    </table>
  `,
})
export class BlockConfigComponent implements OnInit {
  private readonly blockService = inject(BlockService);

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
        blocks: [...blocks].sort((a, b) => a.name.localeCompare(b.name)),
      }));
  });

  ngOnInit(): void {
    this.blockService.getBlocks().subscribe({
      next: (blocks) => this.blocks.set(blocks),
      error: () => this.error.set('Failed to load blocks.'),
    });
  }

  startEdit(block: BlockResponse): void {
    this.editingBlockId.set(block.id);
    this.editValue.set(block.traversal_time_seconds);
    this.validationError.set(null);
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

  onBlur(): void {
    this.cancelEdit();
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
