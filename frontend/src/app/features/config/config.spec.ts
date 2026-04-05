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

  it('should render block config and vehicle list sections', () => {
    const fixture = TestBed.createComponent(ConfigComponent);
    fixture.detectChanges();

    httpTesting.expectOne((req) => req.url.endsWith('/blocks'));
    httpTesting.expectOne((req) => req.url.endsWith('/vehicles'));

    expect(fixture.nativeElement.querySelector('app-block-config')).toBeTruthy();
    expect(fixture.nativeElement.querySelector('app-vehicle-list')).toBeTruthy();
  });
});
