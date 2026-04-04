import { Component } from '@angular/core';
import { BlockConfigComponent } from './block-config';
import { TrackMapOverviewComponent } from './track-map-overview';

@Component({
  selector: 'app-config',
  imports: [BlockConfigComponent, TrackMapOverviewComponent],
  template: `
    <div class="mb-8">
      <app-block-config />
    </div>

    <div>
      <h2 class="mb-4 text-xl font-semibold">Track Map</h2>
      <app-track-map-overview />
    </div>
  `,
})
export class ConfigComponent {}
