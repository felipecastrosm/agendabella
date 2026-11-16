import { Component, input } from '@angular/core';

@Component({
  selector: 'app-cabecalho',
  template: `
    <header class="topo">
      <p class="salao">Studio Bella Cabelos</p>
      <p class="sub">{{ subtitulo() }}</p>
    </header>
    @if (passo()) {
      <div class="passos" role="status">
        Passo {{ passo() }} de 3
        <div class="barra" aria-hidden="true"><i [style.width.%]="(passo()! / 3) * 100"></i></div>
      </div>
    }
  `,
})
export class Cabecalho {
  readonly subtitulo = input('Agende seu horário');
  readonly passo = input<number | null>(null);
}
