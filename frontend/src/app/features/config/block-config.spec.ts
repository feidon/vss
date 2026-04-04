import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { BlockConfigComponent } from './block-config';
import { BlockResponse } from '../../shared/models';

const UNGROUPED_BLOCK: BlockResponse = {
  id: 'b1',
  name: 'B1',
  group: 0,
  traversal_time_seconds: 30,
};

const GROUPED_BLOCK: BlockResponse = {
  id: 'b3',
  name: 'B3',
  group: 2,
  traversal_time_seconds: 45,
};

describe('BlockConfigComponent', () => {
  let httpTesting: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [BlockConfigComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  function createAndLoad(blocks: BlockResponse[]) {
    const fixture = TestBed.createComponent(BlockConfigComponent);
    fixture.detectChanges();
    httpTesting.expectOne((req) => req.url.endsWith('/blocks')).flush(blocks);
    fixture.detectChanges();
    return fixture;
  }

  function getGroupCells(fixture: ReturnType<typeof createAndLoad>): string[] {
    const rows = fixture.nativeElement.querySelectorAll(
      'tr.border-b.hover\\:bg-gray-50',
    ) as NodeListOf<HTMLTableRowElement>;
    return Array.from(rows).map(
      (row) => (row.querySelectorAll('td')[1] as HTMLTableCellElement).textContent?.trim() ?? '',
    );
  }

  it('should display "-" in group column for ungrouped blocks (group 0)', () => {
    const fixture = createAndLoad([UNGROUPED_BLOCK]);
    const groupCells = getGroupCells(fixture);
    expect(groupCells[0]).toBe('-');
  });

  it('should display numeric group value for grouped blocks', () => {
    const fixture = createAndLoad([GROUPED_BLOCK]);
    const groupCells = getGroupCells(fixture);
    expect(groupCells[0]).toBe('2');
  });

  it('should save on blur with valid value', () => {
    const fixture = createAndLoad([GROUPED_BLOCK]);
    const component = fixture.componentInstance;

    component.startEdit(GROUPED_BLOCK);
    component.editValue.set(60);
    fixture.detectChanges();

    component.onBlur(GROUPED_BLOCK);
    fixture.detectChanges();

    const req = httpTesting.expectOne((r) => r.url.endsWith(`/blocks/${GROUPED_BLOCK.id}`));
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ traversal_time_seconds: 60 });
    req.flush({ id: GROUPED_BLOCK.id });

    expect(component.editingBlockId()).toBeNull();
  });

  it('should keep edit open on blur with invalid value', () => {
    const fixture = createAndLoad([GROUPED_BLOCK]);
    const component = fixture.componentInstance;

    component.startEdit(GROUPED_BLOCK);
    component.editValue.set(0);
    fixture.detectChanges();

    component.onBlur(GROUPED_BLOCK);
    fixture.detectChanges();

    httpTesting.expectNone((r) => r.url.endsWith(`/blocks/${GROUPED_BLOCK.id}`));
    expect(component.editingBlockId()).toBe(GROUPED_BLOCK.id);
    expect(component.validationError()).toBe('Must be a positive integer (≥ 1).');
  });

  it('should cancel without saving on Escape', () => {
    const fixture = createAndLoad([GROUPED_BLOCK]);
    const component = fixture.componentInstance;

    component.startEdit(GROUPED_BLOCK);
    component.editValue.set(99);
    fixture.detectChanges();

    component.onKeydown(new KeyboardEvent('keydown', { key: 'Escape' }), GROUPED_BLOCK);
    fixture.detectChanges();

    httpTesting.expectNone((r) => r.url.endsWith(`/blocks/${GROUPED_BLOCK.id}`));
    expect(component.editingBlockId()).toBeNull();
  });
});
