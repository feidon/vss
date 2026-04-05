import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Component, signal } from '@angular/core';
import { ConflictAlertComponent } from './conflict-alert';
import { ConflictResponse, GraphResponse } from '../../shared/models';

const mockGraph: GraphResponse = {
  nodes: [
    { type: 'platform', id: 'p1', name: 'P1A', x: 0, y: 0 },
    { type: 'platform', id: 'p2', name: 'P2A', x: 2, y: 0 },
  ],
  junctions: [],
  edges: [
    { id: 'b3', name: 'B3', from_id: 'p1', to_id: 'p2' },
    { id: 'b7', name: 'B7', from_id: 'p1', to_id: 'p2' },
    { id: 'b8', name: 'B8', from_id: 'p2', to_id: 'p1' },
  ],
  stations: [],
  vehicles: [{ id: 'v1', name: 'V1' }],
};

@Component({
  imports: [ConflictAlertComponent],
  template: `<app-conflict-alert
    [conflicts]="conflicts()"
    [graph]="graph()"
    (dismiss)="dismissed = true"
  />`,
})
class TestHostComponent {
  conflicts = signal<ConflictResponse>({
    vehicle_conflicts: [],
    block_conflicts: [],
    interlocking_conflicts: [],
    battery_conflicts: [],
  });
  graph = signal<GraphResponse>(mockGraph);
  dismissed = false;
}

describe('ConflictAlertComponent', () => {
  let fixture: ComponentFixture<TestHostComponent>;
  let host: TestHostComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TestHostComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(TestHostComponent);
    host = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should display vehicle name instead of UUID', () => {
    host.conflicts.set({
      vehicle_conflicts: [
        {
          vehicle_id: 'v1',
          service_a_id: 101,
          service_b_id: 102,
          reason: 'Overlapping time windows',
        },
      ],
      block_conflicts: [],
      interlocking_conflicts: [],
      battery_conflicts: [],
    });
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent;
    expect(text).toContain('V1');
    expect(text).toContain('S101');
    expect(text).toContain('S102');
    expect(text).toContain('Overlapping time windows');
    expect(text).not.toContain('v1');
  });

  it('should display block name instead of UUID', () => {
    host.conflicts.set({
      vehicle_conflicts: [],
      block_conflicts: [
        {
          block_id: 'b3',
          service_a_id: 101,
          service_b_id: 102,
          overlap_start: 1700000000,
          overlap_end: 1700000030,
        },
      ],
      interlocking_conflicts: [],
      battery_conflicts: [],
    });
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent;
    expect(text).toContain('B3');
    expect(text).toContain('S101');
    expect(text).toContain('S102');
  });

  it('should display interlocking conflict with block names', () => {
    host.conflicts.set({
      vehicle_conflicts: [],
      block_conflicts: [],
      interlocking_conflicts: [
        {
          group: 3,
          block_a_id: 'b7',
          block_b_id: 'b8',
          service_a_id: 101,
          service_b_id: 102,
          overlap_start: 1700000000,
          overlap_end: 1700000030,
        },
      ],
      battery_conflicts: [],
    });
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent;
    expect(text).toContain('Group 3');
    expect(text).toContain('B7');
    expect(text).toContain('B8');
    expect(text).toContain('S101');
    expect(text).toContain('S102');
  });

  it('should display service names with S prefix for battery conflicts', () => {
    host.conflicts.set({
      vehicle_conflicts: [],
      block_conflicts: [],
      interlocking_conflicts: [],
      battery_conflicts: [{ type: 'low_battery', service_id: 201 }],
    });
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent;
    expect(text).toContain('S201');
    expect(text).toContain('insufficient battery');
  });

  it('should fall back to raw ID when node not found in graph', () => {
    host.conflicts.set({
      vehicle_conflicts: [],
      block_conflicts: [
        {
          block_id: 'unknown-uuid',
          service_a_id: 101,
          service_b_id: 102,
          overlap_start: 1700000000,
          overlap_end: 1700000030,
        },
      ],
      interlocking_conflicts: [],
      battery_conflicts: [],
    });
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent;
    expect(text).toContain('unknown-uuid');
  });

  it('should fall back to raw ID when vehicle not found in graph', () => {
    host.conflicts.set({
      vehicle_conflicts: [
        { vehicle_id: 'unknown-vehicle', service_a_id: 101, service_b_id: 102, reason: 'Overlap' },
      ],
      block_conflicts: [],
      interlocking_conflicts: [],
      battery_conflicts: [],
    });
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent;
    expect(text).toContain('unknown-vehicle');
  });
});
