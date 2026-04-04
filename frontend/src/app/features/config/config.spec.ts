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

    httpTesting.expectOne((req) => req.url.endsWith('/blocks'));

    expect(fixture.nativeElement.querySelector('app-block-config')).toBeTruthy();
  });
});
