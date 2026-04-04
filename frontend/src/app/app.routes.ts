import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: 'schedule', pathMatch: 'full' },
  {
    path: 'schedule',
    loadComponent: () =>
      import('./features/schedule/schedule-page').then((m) => m.SchedulePageComponent),
    children: [
      {
        path: '',
        loadComponent: () =>
          import('./features/schedule/schedule-list').then((m) => m.ScheduleListComponent),
      },
      {
        path: ':id/edit',
        loadComponent: () =>
          import('./features/schedule/schedule-editor').then((m) => m.ScheduleEditorComponent),
      },
    ],
  },
  {
    path: 'config',
    loadComponent: () => import('./features/config/config').then((m) => m.ConfigComponent),
  },
];
