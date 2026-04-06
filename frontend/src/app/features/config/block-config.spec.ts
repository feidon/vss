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
      'tr.h-10',
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

  it('should send only one PATCH when Enter triggers save followed by blur on input removal', () => {
    const fixture = createAndLoad([GROUPED_BLOCK]);
    const component = fixture.componentInstance;

    component.startEdit(GROUPED_BLOCK);
    component.editValue.set(60);
    fixture.detectChanges();

    // Simulate the real-world sequence: Enter key triggers save, then the input
    // is removed from the DOM (via editingBlockId=null), which fires blur on the
    // previously focused input → onBlur is called again.
    component.onKeydown(new KeyboardEvent('keydown', { key: 'Enter' }), GROUPED_BLOCK);
    component.onBlur(GROUPED_BLOCK);
    fixture.detectChanges();

    const reqs = httpTesting.match((r) => r.url.endsWith(`/blocks/${GROUPED_BLOCK.id}`));
    expect(reqs.length).toBe(1);
    reqs[0].flush({ id: GROUPED_BLOCK.id });
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

  it('should render blocks sorted by name within each group', () => {
    const blocks: BlockResponse[] = [
      { id: 'b4', name: 'B4', group: 2, traversal_time_seconds: 20 },
      { id: 'b3', name: 'B3', group: 2, traversal_time_seconds: 15 },
      { id: 'b9', name: 'B9', group: 3, traversal_time_seconds: 25 },
      { id: 'b7', name: 'B7', group: 3, traversal_time_seconds: 30 },
    ];
    const fixture = createAndLoad(blocks);
    const rows = fixture.nativeElement.querySelectorAll(
      'tr.h-10',
    ) as NodeListOf<HTMLTableRowElement>;
    const names = Array.from(rows).map(
      (row) => (row.querySelectorAll('td')[0] as HTMLTableCellElement).textContent?.trim() ?? '',
    );
    // Group 2 first (lower number), then Group 3; sorted within each group
    expect(names).toEqual(['B3', 'B4', 'B7', 'B9']);
  });

  it('should sort Group 2 blocks in natural numeric order (B3, B4, B13, B14)', () => {
    const blocks: BlockResponse[] = [
      { id: 'b14', name: 'B14', group: 2, traversal_time_seconds: 20 },
      { id: 'b3', name: 'B3', group: 2, traversal_time_seconds: 15 },
      { id: 'b13', name: 'B13', group: 2, traversal_time_seconds: 25 },
      { id: 'b4', name: 'B4', group: 2, traversal_time_seconds: 30 },
    ];
    const fixture = createAndLoad(blocks);
    const rows = fixture.nativeElement.querySelectorAll(
      'tr.h-10',
    ) as NodeListOf<HTMLTableRowElement>;
    const names = Array.from(rows).map(
      (row) => (row.querySelectorAll('td')[0] as HTMLTableCellElement).textContent?.trim() ?? '',
    );
    expect(names).toEqual(['B3', 'B4', 'B13', 'B14']);
  });

  it('should sort Group 3 blocks in natural numeric order (B7, B8, B9, B10)', () => {
    const blocks: BlockResponse[] = [
      { id: 'b10', name: 'B10', group: 3, traversal_time_seconds: 20 },
      { id: 'b8', name: 'B8', group: 3, traversal_time_seconds: 15 },
      { id: 'b7', name: 'B7', group: 3, traversal_time_seconds: 25 },
      { id: 'b9', name: 'B9', group: 3, traversal_time_seconds: 30 },
    ];
    const fixture = createAndLoad(blocks);
    const rows = fixture.nativeElement.querySelectorAll(
      'tr.h-10',
    ) as NodeListOf<HTMLTableRowElement>;
    const names = Array.from(rows).map(
      (row) => (row.querySelectorAll('td')[0] as HTMLTableCellElement).textContent?.trim() ?? '',
    );
    expect(names).toEqual(['B7', 'B8', 'B9', 'B10']);
  });

  it('should focus input when editing starts', async () => {
    const fixture = createAndLoad([GROUPED_BLOCK]);
    const component = fixture.componentInstance;

    component.startEdit(GROUPED_BLOCK);
    fixture.detectChanges();
    await fixture.whenStable();

    const input = fixture.nativeElement.querySelector('input[type="number"]') as HTMLInputElement;
    expect(input).toBeTruthy();
    expect(document.activeElement).toBe(input);

    // Clean up: save to avoid dangling PATCH
    component.onBlur(GROUPED_BLOCK);
    fixture.detectChanges();
    httpTesting.expectOne((r) => r.url.endsWith(`/blocks/${GROUPED_BLOCK.id}`)).flush({});
  });

  it('should resolve block UUID in structured error message on update failure', () => {
    const fixture = createAndLoad([GROUPED_BLOCK]);
    const component = fixture.componentInstance;

    component.startEdit(GROUPED_BLOCK);
    component.editValue.set(60);
    fixture.detectChanges();

    component.onBlur(GROUPED_BLOCK);
    fixture.detectChanges();

    httpTesting
      .expectOne((r) => r.url.endsWith(`/blocks/${GROUPED_BLOCK.id}`))
      .flush(
        {
          detail: {
            error_code: 'INVALID_TRAVERSAL_TIME',
            message: `Invalid traversal time for block ${GROUPED_BLOCK.id}`,
            context: { block_id: GROUPED_BLOCK.id },
          },
        },
        { status: 400, statusText: 'Bad Request' },
      );
    fixture.detectChanges();

    expect(component.error()).toBe('Invalid traversal time');
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
