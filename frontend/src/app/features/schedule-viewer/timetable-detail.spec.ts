import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TimetableDetailComponent } from './timetable-detail';
import { ServiceResponse } from '../../shared/models';

describe('TimetableDetailComponent', () => {
  let fixture: ComponentFixture<TimetableDetailComponent>;

  const serviceWithTimetable: ServiceResponse = {
    id: 101,
    name: 'S101',
    vehicle_id: 'v1',
    path: [
      { type: 'platform', id: 'p1', name: 'P1A' },
      { type: 'block', id: 'b1', name: 'B1', group: 1, traversal_time_seconds: 30 },
      { type: 'platform', id: 'p2', name: 'P2A' },
    ],
    timetable: [
      { order: 0, node_id: 'p1', arrival: 1700000000, departure: 1700000030 },
      { order: 2, node_id: 'p2', arrival: 1700000090, departure: 1700000120 },
      { order: 1, node_id: 'b1', arrival: 1700000030, departure: 1700000090 },
    ],
  };

  const serviceNoTimetable: ServiceResponse = {
    id: 102,
    name: 'S102',
    vehicle_id: 'v2',
    path: [],
    timetable: [],
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TimetableDetailComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(TimetableDetailComponent);
  });

  it('should display service header with name and vehicle', async () => {
    fixture.componentRef.setInput('service', serviceWithTimetable);
    fixture.componentRef.setInput('vehicleName', 'V1');
    await fixture.whenStable();

    expect(fixture.nativeElement.textContent).toContain('S101');
    expect(fixture.nativeElement.textContent).toContain('V1');
  });

  it('should show empty message when no timetable entries', async () => {
    fixture.componentRef.setInput('service', serviceNoTimetable);
    fixture.componentRef.setInput('vehicleName', 'V2');
    await fixture.whenStable();

    expect(fixture.nativeElement.textContent).toContain('No timetable');
  });

  it('should display timetable entries sorted by order', async () => {
    fixture.componentRef.setInput('service', serviceWithTimetable);
    fixture.componentRef.setInput('vehicleName', 'V1');
    await fixture.whenStable();

    const rows = fixture.nativeElement.querySelectorAll('tbody tr');
    expect(rows).toHaveLength(3);
    // First row should be order 0 (P1A), second order 1 (B1), third order 2 (P2A)
    expect(rows[0].textContent).toContain('P1A');
    expect(rows[1].textContent).toContain('B1');
    expect(rows[2].textContent).toContain('P2A');
  });

  it('should show node type for each entry', async () => {
    fixture.componentRef.setInput('service', serviceWithTimetable);
    fixture.componentRef.setInput('vehicleName', 'V1');
    await fixture.whenStable();

    const rows = fixture.nativeElement.querySelectorAll('tbody tr');
    expect(rows[0].textContent).toContain('platform');
    expect(rows[1].textContent).toContain('block');
  });

  it('should highlight platform rows', async () => {
    fixture.componentRef.setInput('service', serviceWithTimetable);
    fixture.componentRef.setInput('vehicleName', 'V1');
    await fixture.whenStable();

    const rows = fixture.nativeElement.querySelectorAll('tbody tr');
    // Platform rows (0 and 2) should have bg-blue-50
    expect(rows[0].classList.contains('bg-blue-50')).toBe(true);
    expect(rows[1].classList.contains('bg-blue-50')).toBe(false);
    expect(rows[2].classList.contains('bg-blue-50')).toBe(true);
  });

  it('should format epoch times via EpochTimePipe', async () => {
    fixture.componentRef.setInput('service', serviceWithTimetable);
    fixture.componentRef.setInput('vehicleName', 'V1');
    await fixture.whenStable();

    const rows = fixture.nativeElement.querySelectorAll('tbody tr');
    // Times should be HH:mm:ss format, not raw epoch
    const text = rows[0].textContent;
    expect(text).not.toContain('1700000000');
    expect(text).toMatch(/\d{2}:\d{2}:\d{2}/);
  });

  it('should emit back event on back button click', async () => {
    fixture.componentRef.setInput('service', serviceWithTimetable);
    fixture.componentRef.setInput('vehicleName', 'V1');
    await fixture.whenStable();

    let emitted = false;
    fixture.componentInstance.back.subscribe(() => (emitted = true));

    const btn = fixture.nativeElement.querySelector('button') as HTMLButtonElement;
    btn.click();
    expect(emitted).toBe(true);
  });
});
