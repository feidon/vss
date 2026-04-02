import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: 'editor', pathMatch: 'full' },
  {
    path: 'editor',
    loadComponent: () =>
      import('./features/schedule-editor/schedule-editor').then((m) => m.ScheduleEditorComponent),
  },
  {
    path: 'viewer',
    loadComponent: () =>
      import('./features/schedule-viewer/schedule-viewer').then((m) => m.ScheduleViewerComponent),
  },
  {
    path: 'blocks',
    loadComponent: () =>
      import('./features/block-config/block-config').then((m) => m.BlockConfigComponent),
  },
  {
    path: 'map',
    loadComponent: () => import('./features/track-map/track-map').then((m) => m.TrackMapComponent),
  },
];
