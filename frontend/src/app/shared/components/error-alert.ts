import { Component, input, output } from '@angular/core';

@Component({
  selector: 'app-error-alert',
  template: `
    <div class="relative mb-4 rounded border border-red-300 bg-red-50 p-4 text-sm text-red-800">
      <button
        class="absolute right-2 top-2 text-red-400 hover:text-red-600"
        (click)="dismiss.emit()"
      >
        &times;
      </button>
      <span>{{ message() }}</span>
    </div>
  `,
})
export class ErrorAlertComponent {
  readonly message = input.required<string>();
  readonly dismiss = output<void>();
}
