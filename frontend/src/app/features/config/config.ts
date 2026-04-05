import { Component } from '@angular/core';
import { BlockConfigComponent } from './block-config';
import { VehicleListComponent } from './vehicle-list';

@Component({
  selector: 'app-config',
  imports: [BlockConfigComponent, VehicleListComponent],
  template: `
    <app-block-config />
    <div class="mt-10">
      <app-vehicle-list />
    </div>
  `,
})
export class ConfigComponent {}
