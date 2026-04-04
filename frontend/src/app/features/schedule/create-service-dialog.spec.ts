import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { DialogRef } from '@angular/cdk/dialog';
import { CreateServiceDialogComponent } from './create-service-dialog';
import { API_BASE_URL } from '../../core/services/api.config';

describe('CreateServiceDialogComponent', () => {
  let httpTesting: HttpTestingController;
  let dialogRefSpy: { close: ReturnType<typeof vi.fn> };

  beforeEach(async () => {
    dialogRefSpy = { close: vi.fn() };

    await TestBed.configureTestingModule({
      imports: [CreateServiceDialogComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: DialogRef, useValue: dialogRefSpy },
      ],
    }).compileComponents();

    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('should load vehicles on init', () => {
    const fixture = TestBed.createComponent(CreateServiceDialogComponent);
    fixture.detectChanges();

    const req = httpTesting.expectOne(`${API_BASE_URL}/vehicles`);
    req.flush([{ id: 'v1', name: 'V1' }]);
    fixture.detectChanges();

    const select = fixture.nativeElement.querySelector('select');
    expect(select.disabled).toBe(false);
    expect(select.textContent).toContain('V1');
  });

  it('should show validation errors when submitting empty form', () => {
    const fixture = TestBed.createComponent(CreateServiceDialogComponent);
    fixture.detectChanges();
    httpTesting.expectOne(`${API_BASE_URL}/vehicles`).flush([]);

    const form = fixture.nativeElement.querySelector('form');
    form.dispatchEvent(new Event('submit'));
    fixture.detectChanges();

    const errors = fixture.nativeElement.querySelectorAll('.text-red-500');
    expect(errors.length).toBeGreaterThan(0);
  });

  it('should close dialog on cancel', () => {
    const fixture = TestBed.createComponent(CreateServiceDialogComponent);
    fixture.detectChanges();
    httpTesting.expectOne(`${API_BASE_URL}/vehicles`).flush([]);

    const cancelBtn = fixture.nativeElement.querySelector('button[type="button"]');
    cancelBtn.click();

    expect(dialogRefSpy.close).toHaveBeenCalledWith();
  });

  it('should show error when vehicles fail to load', () => {
    const fixture = TestBed.createComponent(CreateServiceDialogComponent);
    fixture.detectChanges();

    httpTesting
      .expectOne(`${API_BASE_URL}/vehicles`)
      .flush(null, { status: 500, statusText: 'Error' });
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Failed to load vehicles');
  });
});
