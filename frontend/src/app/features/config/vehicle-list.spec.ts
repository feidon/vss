import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { VehicleListComponent } from './vehicle-list';
import { Vehicle } from '../../shared/models';

const VEHICLES: Vehicle[] = [
  { id: 'v3', name: 'V3' },
  { id: 'v1', name: 'V1' },
  { id: 'v2', name: 'V2' },
];

describe('VehicleListComponent', () => {
  let httpTesting: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VehicleListComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  function createAndLoad(vehicles: Vehicle[]) {
    const fixture = TestBed.createComponent(VehicleListComponent);
    fixture.detectChanges();
    httpTesting.expectOne((req) => req.url.endsWith('/vehicles')).flush(vehicles);
    fixture.detectChanges();
    return fixture;
  }

  function getVehicleNames(fixture: ReturnType<typeof createAndLoad>): string[] {
    const rows = fixture.nativeElement.querySelectorAll(
      'tr.h-10',
    ) as NodeListOf<HTMLTableRowElement>;
    return Array.from(rows).map(
      (row) => (row.querySelector('td') as HTMLTableCellElement).textContent?.trim() ?? '',
    );
  }

  it('should display vehicles sorted by name in natural alphanumeric order', () => {
    const fixture = createAndLoad(VEHICLES);
    expect(getVehicleNames(fixture)).toEqual(['V1', 'V2', 'V3']);
  });

  it('should show loading state before data arrives', () => {
    const fixture = TestBed.createComponent(VehicleListComponent);
    fixture.detectChanges();

    const loadingText = fixture.nativeElement.textContent;
    expect(loadingText).toContain('Loading vehicles...');

    httpTesting.expectOne((req) => req.url.endsWith('/vehicles')).flush([]);
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).not.toContain('Loading vehicles...');
  });

  it('should display error message on API failure', () => {
    const fixture = TestBed.createComponent(VehicleListComponent);
    fixture.detectChanges();

    httpTesting
      .expectOne((req) => req.url.endsWith('/vehicles'))
      .flush('Server error', { status: 500, statusText: 'Internal Server Error' });
    fixture.detectChanges();

    const errorAlert = fixture.nativeElement.querySelector('app-error-alert');
    expect(errorAlert).toBeTruthy();
    expect(fixture.componentInstance.error()).toBe('Failed to load vehicles.');
  });

  it('should render correct number of vehicle rows', () => {
    const fixture = createAndLoad(VEHICLES);
    const rows = fixture.nativeElement.querySelectorAll('tr.h-10');
    expect(rows.length).toBe(3);
  });

  it('should handle natural sort with double-digit names', () => {
    const vehicles: Vehicle[] = [
      { id: 'v10', name: 'V10' },
      { id: 'v2', name: 'V2' },
      { id: 'v1', name: 'V1' },
    ];
    const fixture = createAndLoad(vehicles);
    expect(getVehicleNames(fixture)).toEqual(['V1', 'V2', 'V10']);
  });
});
