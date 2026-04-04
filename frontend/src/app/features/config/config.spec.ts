import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ConfigComponent } from './config';

describe('ConfigComponent', () => {
  let httpTesting: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ConfigComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('should render block config section', () => {
    const fixture = TestBed.createComponent(ConfigComponent);
    fixture.detectChanges();

    // BlockConfigComponent requests blocks
    httpTesting.expectOne((req) => req.url.endsWith('/blocks'));
    // TrackMapOverviewComponent requests graph
    httpTesting.expectOne((req) => req.url.endsWith('/graph'));

    expect(fixture.nativeElement.querySelector('app-block-config')).toBeTruthy();
  });

  it('should render track map section', () => {
    const fixture = TestBed.createComponent(ConfigComponent);
    fixture.detectChanges();

    httpTesting.expectOne((req) => req.url.endsWith('/blocks'));
    httpTesting.expectOne((req) => req.url.endsWith('/graph'));

    expect(fixture.nativeElement.textContent).toContain('Track Map');
    expect(fixture.nativeElement.querySelector('app-track-map-overview')).toBeTruthy();
  });
});
