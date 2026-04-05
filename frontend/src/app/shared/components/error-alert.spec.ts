import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Component, signal } from '@angular/core';
import { ErrorAlertComponent } from './error-alert';

@Component({
  imports: [ErrorAlertComponent],
  template: `<app-error-alert [message]="message()" (dismiss)="dismissed = true" />`,
})
class TestHostComponent {
  message = signal('Test error message');
  dismissed = false;
}

describe('ErrorAlertComponent', () => {
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

  it('should display the error message', () => {
    expect(fixture.nativeElement.textContent).toContain('Test error message');
  });

  it('should update when message changes', () => {
    host.message.set('Updated error');
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Updated error');
  });

  it('should emit dismiss when close button is clicked', () => {
    const btn = fixture.nativeElement.querySelector('button');
    btn.click();
    expect(host.dismissed).toBe(true);
  });
});
