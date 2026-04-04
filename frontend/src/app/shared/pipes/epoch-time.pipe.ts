import { Pipe, PipeTransform } from '@angular/core';
import { epochToDisplayTime } from '../utils/time-utils';

@Pipe({ name: 'epochTime', standalone: true })
export class EpochTimePipe implements PipeTransform {
  transform(value: number): string {
    return epochToDisplayTime(value);
  }
}
