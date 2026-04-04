import { Component } from '@angular/core';
import { BlockConfigComponent } from './block-config';

@Component({
  selector: 'app-config',
  imports: [BlockConfigComponent],
  template: `<app-block-config />`,
})
export class ConfigComponent {}
