import { Component, input, output } from '@angular/core';

@Component({
  selector: 'app-error-alert',
  template: `
    <div
      class="animate-fade-in relative mb-4 flex items-start gap-3 rounded-lg border border-signal-danger/25 bg-signal-danger/5 p-4 text-base text-signal-danger shadow-[0_0_16px_var(--color-glow-red)]"
    >
      <svg class="mt-0.5 h-4 w-4 shrink-0" viewBox="0 0 16 16" fill="currentColor">
        <path
          d="M8 1a7 7 0 100 14A7 7 0 008 1zm-.75 3.75a.75.75 0 011.5 0v3.5a.75.75 0 01-1.5 0v-3.5zM8 11a1 1 0 100 2 1 1 0 000-2z"
        />
      </svg>
      <span class="flex-1 font-display font-medium">{{ message() }}</span>
      <button
        class="shrink-0 rounded p-0.5 text-signal-danger/60 transition-colors hover:bg-signal-danger/10 hover:text-signal-danger"
        (click)="dismiss.emit()"
      >
        <svg class="h-4 w-4" viewBox="0 0 16 16" fill="currentColor">
          <path
            d="M3.72 3.72a.75.75 0 011.06 0L8 6.94l3.22-3.22a.75.75 0 111.06 1.06L9.06 8l3.22 3.22a.75.75 0 11-1.06 1.06L8 9.06l-3.22 3.22a.75.75 0 01-1.06-1.06L6.94 8 3.72 4.78a.75.75 0 010-1.06z"
          />
        </svg>
      </button>
    </div>
  `,
})
export class ErrorAlertComponent {
  readonly message = input.required<string>();
  readonly dismiss = output<void>();
}
