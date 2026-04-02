import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ServiceFormComponent } from './service-form';
import { Vehicle } from '../../shared/models';
import { API_BASE_URL } from '../../core/services/api.config';

describe('ServiceFormComponent', () => {
  let fixture: ComponentFixture<ServiceFormComponent>;
  let httpTesting: HttpTestingController;

  const vehicles: Vehicle[] = [
    { id: 'v1', name: 'V1' },
    { id: 'v2', name: 'V2' },
  ];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ServiceFormComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(ServiceFormComponent);
    httpTesting = TestBed.inject(HttpTestingController);
    fixture.componentRef.setInput('vehicles', vehicles);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('should render vehicle options', async () => {
    await fixture.whenStable();
    const options = fixture.nativeElement.querySelectorAll('option');
    // First option is "Select vehicle" placeholder + 2 vehicles
    expect(options.length).toBe(3);
    expect(options[1].textContent.trim()).toBe('V1');
  });

  it('should disable submit when name is empty', async () => {
    await fixture.whenStable();
    const btn = fixture.nativeElement.querySelector('button[type="submit"]') as HTMLButtonElement;
    expect(btn.disabled).toBe(true);
  });

  it('should create service and emit id', async () => {
    fixture.componentInstance.name.set('S101');
    fixture.componentInstance.vehicleId.set('v1');
    await fixture.whenStable();

    let emittedId: number | undefined;
    fixture.componentInstance.created.subscribe((id: number) => (emittedId = id));

    fixture.componentInstance.onSubmit();

    const req = httpTesting.expectOne(`${API_BASE_URL}/services`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ name: 'S101', vehicle_id: 'v1' });
    req.flush({ id: 101 });

    expect(emittedId).toBe(101);
  });
});
