import { TestBed } from '@angular/core/testing';
import { DialogRef, DIALOG_DATA } from '@angular/cdk/dialog';
import { ConfirmDialogComponent } from './confirm-dialog';

describe('ConfirmDialogComponent', () => {
  let dialogRefSpy: { close: ReturnType<typeof vi.fn> };

  beforeEach(async () => {
    dialogRefSpy = { close: vi.fn() };

    await TestBed.configureTestingModule({
      imports: [ConfirmDialogComponent],
      providers: [
        { provide: DialogRef, useValue: dialogRefSpy },
        { provide: DIALOG_DATA, useValue: { message: 'Delete this?' } },
      ],
    }).compileComponents();
  });

  it('should display the message', () => {
    const fixture = TestBed.createComponent(ConfirmDialogComponent);
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Delete this?');
  });

  it('should close with true on confirm', () => {
    const fixture = TestBed.createComponent(ConfirmDialogComponent);
    fixture.detectChanges();

    const buttons = fixture.nativeElement.querySelectorAll('button');
    const confirmBtn = Array.from(buttons as NodeListOf<HTMLButtonElement>).find(
      (b) => b.textContent?.trim() === 'Confirm',
    )!;
    confirmBtn.click();

    expect(dialogRefSpy.close).toHaveBeenCalledWith(true);
  });

  it('should close with false on cancel', () => {
    const fixture = TestBed.createComponent(ConfirmDialogComponent);
    fixture.detectChanges();

    const buttons = fixture.nativeElement.querySelectorAll('button');
    const cancelBtn = Array.from(buttons as NodeListOf<HTMLButtonElement>).find(
      (b) => b.textContent?.trim() === 'Cancel',
    )!;
    cancelBtn.click();

    expect(dialogRefSpy.close).toHaveBeenCalledWith(false);
  });
});
