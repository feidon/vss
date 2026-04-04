import { Component, inject, OnInit, signal } from '@angular/core';
import { GraphService } from '../../core/services/graph.service';
import { GraphResponse } from '../../shared/models';
import { TrackMapEditorComponent } from '../schedule/track-map-editor';

@Component({
  selector: 'app-track-map-overview',
  imports: [TrackMapEditorComponent],
  template: `
    @if (graph()) {
      <app-track-map-editor [graph]="graph()!" [interactive]="false" />
    } @else if (error()) {
      <p class="text-sm text-red-600">{{ error() }}</p>
    } @else {
      <p class="text-sm text-gray-500">Loading track map...</p>
    }
  `,
})
export class TrackMapOverviewComponent implements OnInit {
  private readonly graphService = inject(GraphService);

  readonly graph = signal<GraphResponse | null>(null);
  readonly error = signal<string | null>(null);

  ngOnInit(): void {
    this.graphService.getGraph().subscribe({
      next: (g) => this.graph.set(g),
      error: () => this.error.set('Failed to load track map data.'),
    });
  }
}
