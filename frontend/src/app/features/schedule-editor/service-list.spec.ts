import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ServiceListComponent } from './service-list';
import { ServiceResponse, Vehicle } from '../../shared/models';

describe('ServiceListComponent', () => {
  let fixture: ComponentFixture<ServiceListComponent>;

  const vehicles: Vehicle[] = [
    { id: 'v1', name: 'V1' },
    { id: 'v2', name: 'V2' },
  ];

  const services: ServiceResponse[] = [{ id: 101, name: 'S101', vehicle_id: 'v1' }];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ServiceListComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ServiceListComponent);
  });

  it('should show empty state when no services', async () => {
    fixture.componentRef.setInput('services', []);
    fixture.componentRef.setInput('vehicles', []);
    await fixture.whenStable();
    expect(fixture.nativeElement.textContent).toContain('No services created yet');
  });

  it('should display service with vehicle name', async () => {
    fixture.componentRef.setInput('services', services);
    fixture.componentRef.setInput('vehicles', vehicles);
    await fixture.whenStable();

    const row = fixture.nativeElement.querySelector('tbody tr') as HTMLElement;
    expect(row.textContent).toContain('S101');
    expect(row.textContent).toContain('V1');
  });

  it('should emit edit event on Edit click', async () => {
    fixture.componentRef.setInput('services', services);
    fixture.componentRef.setInput('vehicles', vehicles);
    await fixture.whenStable();

    let emitted: ServiceResponse | undefined;
    fixture.componentInstance.edit.subscribe((s: ServiceResponse) => (emitted = s));

    const editBtn = fixture.nativeElement.querySelector('button') as HTMLButtonElement;
    editBtn.click();
    expect(emitted).toEqual(services[0]);
  });

  it('should emit delete event on Delete click', async () => {
    fixture.componentRef.setInput('services', services);
    fixture.componentRef.setInput('vehicles', vehicles);
    await fixture.whenStable();

    let emitted: ServiceResponse | undefined;
    fixture.componentInstance.delete.subscribe((s: ServiceResponse) => (emitted = s));

    const buttons = fixture.nativeElement.querySelectorAll(
      'button',
    ) as NodeListOf<HTMLButtonElement>;
    buttons[1].click(); // Delete is second button
    expect(emitted).toEqual(services[0]);
  });
});
