import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { BlockConfigComponent } from './block-config';
import { BlockResponse } from '../../shared/models';
import { API_BASE_URL } from '../../core/services/api.config';

describe('BlockConfigComponent', () => {
  let fixture: ComponentFixture<BlockConfigComponent>;
  let httpTesting: HttpTestingController;

  const mockBlocks: BlockResponse[] = [
    { id: 'b1', name: 'B1', group: 1, traversal_time_seconds: 60 },
    { id: 'b2', name: 'B2', group: 1, traversal_time_seconds: 45 },
    { id: 'b3', name: 'B3', group: 2, traversal_time_seconds: 30 },
    { id: 'b4', name: 'B4', group: 2, traversal_time_seconds: 50 },
    { id: 'b7', name: 'B7', group: 3, traversal_time_seconds: 40 },
  ];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [BlockConfigComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(BlockConfigComponent);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  function flushBlocks(blocks: BlockResponse[] = mockBlocks): void {
    httpTesting.expectOne(`${API_BASE_URL}/blocks`).flush(blocks);
    fixture.detectChanges();
  }

  it('should load blocks on init and render a table', () => {
    fixture.detectChanges();
    flushBlocks();

    const dataRows = fixture.nativeElement.querySelectorAll(
      'tbody tr:not([data-testid="group-header"])',
    );
    expect(dataRows.length).toBe(5);

    const firstRowCells = dataRows[0].querySelectorAll('td');
    expect(firstRowCells[0].textContent.trim()).toBe('B1');
    expect(firstRowCells[1].textContent.trim()).toBe('1');
    expect(firstRowCells[2].textContent.trim()).toContain('60');
  });

  it('should group blocks by interlocking group with headers sorted numerically', () => {
    fixture.detectChanges();
    // Provide blocks out of order to verify sorting
    flushBlocks([
      { id: 'b7', name: 'B7', group: 3, traversal_time_seconds: 40 },
      { id: 'b2', name: 'B2', group: 1, traversal_time_seconds: 45 },
      { id: 'b3', name: 'B3', group: 2, traversal_time_seconds: 30 },
      { id: 'b1', name: 'B1', group: 1, traversal_time_seconds: 60 },
    ]);

    const groupHeaders = fixture.nativeElement.querySelectorAll('[data-testid="group-header"]');
    expect(groupHeaders.length).toBe(3);
    expect(groupHeaders[0].textContent).toContain('Group 1');
    expect(groupHeaders[1].textContent).toContain('Group 2');
    expect(groupHeaders[2].textContent).toContain('Group 3');

    // Blocks within group 1 should be sorted by name: B1 before B2
    const rows = fixture.nativeElement.querySelectorAll(
      'tbody tr:not([data-testid="group-header"])',
    );
    const blockNames = Array.from(rows as NodeListOf<HTMLElement>)
      .map((r) => r.querySelector('td')?.textContent?.trim())
      .filter(Boolean);
    expect(blockNames).toEqual(['B1', 'B2', 'B3', 'B7']);
  });

  it('should enter edit mode when clicking traversal time', () => {
    fixture.detectChanges();
    flushBlocks();

    const span = fixture.nativeElement.querySelector(
      'tbody tr:not([data-testid="group-header"]) td:nth-child(3) span',
    ) as HTMLElement;
    span.click();
    fixture.detectChanges();

    const input = fixture.nativeElement.querySelector('input[type="number"]') as HTMLInputElement;
    expect(input).toBeTruthy();
    expect(input.valueAsNumber).toBe(60);
  });

  it('should save on Enter and exit edit mode', () => {
    fixture.detectChanges();
    flushBlocks();

    const span = fixture.nativeElement.querySelector(
      'tbody tr:not([data-testid="group-header"]) td:nth-child(3) span',
    ) as HTMLElement;
    span.click();
    fixture.detectChanges();

    const input = fixture.nativeElement.querySelector('input[type="number"]') as HTMLInputElement;
    input.valueAsNumber = 90;
    input.dispatchEvent(new Event('input'));
    input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));
    fixture.detectChanges();

    const req = httpTesting.expectOne(`${API_BASE_URL}/blocks/b1`);
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ traversal_time_seconds: 90 });
    req.flush({ id: 'b1' });
    fixture.detectChanges();

    // Should exit edit mode
    const inputAfter = fixture.nativeElement.querySelector('input[type="number"]');
    expect(inputAfter).toBeNull();
  });

  it('should cancel on Escape without API call', () => {
    fixture.detectChanges();
    flushBlocks();

    const span = fixture.nativeElement.querySelector(
      'tbody tr:not([data-testid="group-header"]) td:nth-child(3) span',
    ) as HTMLElement;
    span.click();
    fixture.detectChanges();

    const input = fixture.nativeElement.querySelector('input[type="number"]') as HTMLInputElement;
    input.valueAsNumber = 999;
    input.dispatchEvent(new Event('input'));
    input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    fixture.detectChanges();

    // Should exit edit mode, no PATCH request
    const inputAfter = fixture.nativeElement.querySelector('input[type="number"]');
    expect(inputAfter).toBeNull();

    // Original value should be displayed
    const span2 = fixture.nativeElement.querySelector(
      'tbody tr:not([data-testid="group-header"]) td:nth-child(3) span',
    );
    expect(span2.textContent.trim()).toContain('60');
  });

  it('should save on blur', () => {
    fixture.detectChanges();
    flushBlocks();

    const span = fixture.nativeElement.querySelector(
      'tbody tr:not([data-testid="group-header"]) td:nth-child(3) span',
    ) as HTMLElement;
    span.click();
    fixture.detectChanges();

    const input = fixture.nativeElement.querySelector('input[type="number"]') as HTMLInputElement;
    input.valueAsNumber = 75;
    input.dispatchEvent(new Event('input'));
    input.dispatchEvent(new Event('blur'));
    fixture.detectChanges();

    const req = httpTesting.expectOne(`${API_BASE_URL}/blocks/b1`);
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ traversal_time_seconds: 75 });
    req.flush({ id: 'b1' });
  });

  it('should reject non-positive values and show validation error', () => {
    fixture.detectChanges();
    flushBlocks();

    const span = fixture.nativeElement.querySelector(
      'tbody tr:not([data-testid="group-header"]) td:nth-child(3) span',
    ) as HTMLElement;
    span.click();
    fixture.detectChanges();

    const input = fixture.nativeElement.querySelector('input[type="number"]') as HTMLInputElement;
    input.valueAsNumber = 0;
    input.dispatchEvent(new Event('input'));
    input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));
    fixture.detectChanges();

    // Should show validation error, no PATCH request
    const validationMsg = fixture.nativeElement.querySelector('.text-red-500');
    expect(validationMsg).toBeTruthy();
    expect(validationMsg.textContent).toContain('positive integer');

    // Should still be in edit mode
    expect(fixture.nativeElement.querySelector('input[type="number"]')).toBeTruthy();
  });

  it('should update displayed value on successful save', () => {
    fixture.detectChanges();
    flushBlocks();

    const span = fixture.nativeElement.querySelector(
      'tbody tr:not([data-testid="group-header"]) td:nth-child(3) span',
    ) as HTMLElement;
    span.click();
    fixture.detectChanges();

    const input = fixture.nativeElement.querySelector('input[type="number"]') as HTMLInputElement;
    input.valueAsNumber = 120;
    input.dispatchEvent(new Event('input'));
    input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));
    fixture.detectChanges();

    httpTesting.expectOne(`${API_BASE_URL}/blocks/b1`).flush({ id: 'b1' });
    fixture.detectChanges();

    const updatedSpan = fixture.nativeElement.querySelector(
      'tbody tr:not([data-testid="group-header"]) td:nth-child(3) span',
    );
    expect(updatedSpan.textContent.trim()).toContain('120');
  });

  it('should revert value and show error on failed save', () => {
    fixture.detectChanges();
    flushBlocks();

    const span = fixture.nativeElement.querySelector(
      'tbody tr:not([data-testid="group-header"]) td:nth-child(3) span',
    ) as HTMLElement;
    span.click();
    fixture.detectChanges();

    const input = fixture.nativeElement.querySelector('input[type="number"]') as HTMLInputElement;
    input.valueAsNumber = 120;
    input.dispatchEvent(new Event('input'));
    input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));
    fixture.detectChanges();

    httpTesting
      .expectOne(`${API_BASE_URL}/blocks/b1`)
      .flush('Error', { status: 500, statusText: 'Internal Server Error' });
    fixture.detectChanges();

    // Value should revert to original
    const revertedSpan = fixture.nativeElement.querySelector(
      'tbody tr:not([data-testid="group-header"]) td:nth-child(3) span',
    );
    expect(revertedSpan.textContent.trim()).toContain('60');

    // Error message should be shown
    const errorEl = fixture.nativeElement.querySelector('.text-red-600');
    expect(errorEl).toBeTruthy();
    expect(errorEl.textContent).toContain('Failed to update B1');
  });

  it('should display error message when block loading fails', () => {
    fixture.detectChanges();

    httpTesting
      .expectOne(`${API_BASE_URL}/blocks`)
      .flush('Server error', { status: 500, statusText: 'Internal Server Error' });
    fixture.detectChanges();

    const errorEl = fixture.nativeElement.querySelector('.text-red-600');
    expect(errorEl).toBeTruthy();
    expect(errorEl.textContent).toContain('Failed to load blocks');
  });
});
