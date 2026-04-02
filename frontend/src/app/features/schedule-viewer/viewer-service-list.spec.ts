import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ViewerServiceListComponent } from './viewer-service-list';
import { ServiceResponse, Vehicle } from '../../shared/models';

describe('ViewerServiceListComponent', () => {
  let fixture: ComponentFixture<ViewerServiceListComponent>;

  const vehicles: Vehicle[] = [
    { id: 'v1', name: 'V1' },
    { id: 'v2', name: 'V2' },
  ];

  const services: ServiceResponse[] = [
    {
      id: 101,
      name: 'S101',
      vehicle_id: 'v1',
      path: [
        { type: 'platform', id: 'p1', name: 'P1A' },
        { type: 'block', id: 'b1', name: 'B1', group: 1, traversal_time_seconds: 30 },
        { type: 'platform', id: 'p2', name: 'P2A' },
      ],
      timetable: [],
    },
    {
      id: 102,
      name: 'S102',
      vehicle_id: 'v2',
      path: [
        { type: 'platform', id: 'p3', name: 'P3A' },
      ],
      timetable: [],
    },
  ];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ViewerServiceListComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ViewerServiceListComponent);
  });

  it('should show empty state when no services', async () => {
    fixture.componentRef.setInput('services', []);
    fixture.componentRef.setInput('vehicles', []);
    await fixture.whenStable();
    expect(fixture.nativeElement.textContent).toContain('No services to display');
  });

  it('should display services with vehicle name and stop count', async () => {
    fixture.componentRef.setInput('services', services);
    fixture.componentRef.setInput('vehicles', vehicles);
    await fixture.whenStable();

    const rows = fixture.nativeElement.querySelectorAll('tbody tr');
    expect(rows).toHaveLength(2);
    expect(rows[0].textContent).toContain('S101');
    expect(rows[0].textContent).toContain('V1');
    expect(rows[0].textContent).toContain('2'); // 2 platform stops
    expect(rows[1].textContent).toContain('S102');
    expect(rows[1].textContent).toContain('V2');
    expect(rows[1].textContent).toContain('1'); // 1 platform stop
  });

  it('should resolve unknown vehicle ID as raw UUID', async () => {
    const unknownService: ServiceResponse[] = [
      { id: 200, name: 'S200', vehicle_id: 'unknown-uuid', path: [], timetable: [] },
    ];
    fixture.componentRef.setInput('services', unknownService);
    fixture.componentRef.setInput('vehicles', vehicles);
    await fixture.whenStable();

    const row = fixture.nativeElement.querySelector('tbody tr');
    expect(row.textContent).toContain('unknown-uuid');
  });

  it('should filter services by selected vehicle', async () => {
    fixture.componentRef.setInput('services', services);
    fixture.componentRef.setInput('vehicles', vehicles);
    await fixture.whenStable();

    fixture.componentInstance.vehicleFilter.set('v1');
    fixture.detectChanges();
    await fixture.whenStable();

    const rows = fixture.nativeElement.querySelectorAll('tbody tr');
    expect(rows).toHaveLength(1);
    expect(rows[0].textContent).toContain('S101');
  });

  it('should show all services when filter is cleared', async () => {
    fixture.componentRef.setInput('services', services);
    fixture.componentRef.setInput('vehicles', vehicles);
    fixture.componentInstance.vehicleFilter.set('v1');
    fixture.detectChanges();
    await fixture.whenStable();

    fixture.componentInstance.vehicleFilter.set('');
    fixture.detectChanges();
    await fixture.whenStable();

    const rows = fixture.nativeElement.querySelectorAll('tbody tr');
    expect(rows).toHaveLength(2);
  });

  it('should group services by vehicle when toggle is on', async () => {
    fixture.componentRef.setInput('services', services);
    fixture.componentRef.setInput('vehicles', vehicles);
    fixture.componentInstance.grouped.set(true);
    fixture.detectChanges();
    await fixture.whenStable();

    const headers = fixture.nativeElement.querySelectorAll('h3');
    expect(headers).toHaveLength(2);
    expect(headers[0].textContent).toContain('V1');
    expect(headers[1].textContent).toContain('V2');
  });

  it('should emit select event on row click', async () => {
    fixture.componentRef.setInput('services', services);
    fixture.componentRef.setInput('vehicles', vehicles);
    await fixture.whenStable();

    let emitted: ServiceResponse | undefined;
    fixture.componentInstance.select.subscribe((s: ServiceResponse) => (emitted = s));

    const row = fixture.nativeElement.querySelector('tbody tr') as HTMLElement;
    row.click();
    expect(emitted).toEqual(services[0]);
  });
});
