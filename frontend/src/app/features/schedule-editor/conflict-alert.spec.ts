import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ConflictAlertComponent } from './conflict-alert';
import { ConflictResponse } from '../../shared/models';

describe('ConflictAlertComponent', () => {
  let fixture: ComponentFixture<ConflictAlertComponent>;

  const emptyConflicts: ConflictResponse = {
    message: 'Conflicts detected',
    vehicle_conflicts: [],
    block_conflicts: [],
    interlocking_conflicts: [],
    low_battery_conflicts: [],
    insufficient_charge_conflicts: [],
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ConflictAlertComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ConflictAlertComponent);
  });

  it('should display vehicle conflicts', async () => {
    const conflicts: ConflictResponse = {
      ...emptyConflicts,
      vehicle_conflicts: [
        { vehicle_id: 'v1', service_a_id: 1, service_b_id: 2, reason: 'Overlapping time windows' },
      ],
    };
    fixture.componentRef.setInput('conflicts', conflicts);
    await fixture.whenStable();

    expect(fixture.nativeElement.textContent).toContain('Vehicle Conflicts');
    expect(fixture.nativeElement.textContent).toContain('Overlapping time windows');
  });

  it('should display block conflicts', async () => {
    const conflicts: ConflictResponse = {
      ...emptyConflicts,
      block_conflicts: [
        {
          block_id: 'b3',
          service_a_id: 1,
          service_b_id: 2,
          overlap_start: 1700000000,
          overlap_end: 1700000030,
        },
      ],
    };
    fixture.componentRef.setInput('conflicts', conflicts);
    await fixture.whenStable();

    expect(fixture.nativeElement.textContent).toContain('Block Conflicts');
    expect(fixture.nativeElement.textContent).toContain('b3');
  });

  it('should display interlocking conflicts', async () => {
    const conflicts: ConflictResponse = {
      ...emptyConflicts,
      interlocking_conflicts: [
        {
          group: 2,
          block_a_id: 'b3',
          block_b_id: 'b4',
          service_a_id: 1,
          service_b_id: 2,
          overlap_start: 1700000000,
          overlap_end: 1700000030,
        },
      ],
    };
    fixture.componentRef.setInput('conflicts', conflicts);
    await fixture.whenStable();

    expect(fixture.nativeElement.textContent).toContain('Interlocking Conflicts');
    expect(fixture.nativeElement.textContent).toContain('Group 2');
  });

  it('should display battery conflicts', async () => {
    const conflicts: ConflictResponse = {
      ...emptyConflicts,
      low_battery_conflicts: [{ service_id: 1 }],
      insufficient_charge_conflicts: [{ service_id: 1 }],
    };
    fixture.componentRef.setInput('conflicts', conflicts);
    await fixture.whenStable();

    expect(fixture.nativeElement.textContent).toContain('Low Battery');
    expect(fixture.nativeElement.textContent).toContain('Insufficient Charge');
  });

  it('should display multiple conflict types together', async () => {
    const conflicts: ConflictResponse = {
      ...emptyConflicts,
      vehicle_conflicts: [
        { vehicle_id: 'v1', service_a_id: 1, service_b_id: 2, reason: 'Overlap' },
      ],
      block_conflicts: [
        { block_id: 'b1', service_a_id: 1, service_b_id: 2, overlap_start: 100, overlap_end: 200 },
      ],
    };
    fixture.componentRef.setInput('conflicts', conflicts);
    await fixture.whenStable();

    expect(fixture.nativeElement.textContent).toContain('Vehicle Conflicts');
    expect(fixture.nativeElement.textContent).toContain('Block Conflicts');
  });

  it('should emit dismiss on close button click', async () => {
    fixture.componentRef.setInput('conflicts', emptyConflicts);
    await fixture.whenStable();

    let dismissed = false;
    fixture.componentInstance.dismiss.subscribe(() => (dismissed = true));

    const closeBtn = fixture.nativeElement.querySelector('button') as HTMLButtonElement;
    closeBtn.click();
    expect(dismissed).toBe(true);
  });
});
