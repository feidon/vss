import { Pipe, PipeTransform } from '@angular/core';

@Pipe({ name: 'epochTime', standalone: true })
export class EpochTimePipe implements PipeTransform {
  transform(value: number): string {
    if (!value) {
      return '\u2014';
    }
    const date = new Date(value * 1000);
    const h = String(date.getHours()).padStart(2, '0');
    const m = String(date.getMinutes()).padStart(2, '0');
    const s = String(date.getSeconds()).padStart(2, '0');
    return `${h}:${m}:${s}`;
  }
}
