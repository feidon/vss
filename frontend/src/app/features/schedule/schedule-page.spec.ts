import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { SchedulePageComponent } from './schedule-page';

describe('SchedulePageComponent', () => {
  it('should render router-outlet', () => {
    TestBed.configureTestingModule({
      imports: [SchedulePageComponent],
      providers: [provideRouter([])],
    });

    const fixture = TestBed.createComponent(SchedulePageComponent);
    fixture.detectChanges();

    const outlet = fixture.nativeElement.querySelector('router-outlet');
    expect(outlet).toBeTruthy();
  });
});
