import { AfterViewInit, Component, ElementRef, OnInit, inject, viewChild } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { AgendamentoEstado } from '../core/agendamento-estado.service';
import { dataPorExtenso } from '../core/datas';
import { Cabecalho } from '../shared/cabecalho';

/** Tela 3, alertas e resultados: confirmação ou conflito (RF02, RNF04). */
@Component({
  selector: 'app-resultado',
  imports: [Cabecalho, RouterLink],
  template: `
    <div class="tela">
      <app-cabecalho [passo]="3" />
      <main>
        @if (estado.confirmado(); as ag) {
          <div class="resultado">
            <div class="icone-ok" aria-hidden="true">✓</div>
            <h1 #titulo tabindex="-1" class="texto-ok">Agendamento confirmado!</h1>
          </div>
          <dl class="caixa ok">
            <div class="linha"><dt>Serviço</dt><dd>{{ ag.servico }}</dd></div>
            <div class="linha"><dt>Profissional</dt><dd>{{ ag.profissional }}</dd></div>
            <div class="linha"><dt>Data</dt><dd>{{ extenso(ag.data) }}</dd></div>
            <div class="linha"><dt>Horário</dt><dd>{{ ag.hora_inicio }}</dd></div>
          </dl>
          <p class="nota">Em caso de imprevisto, avise o salão pelo WhatsApp.</p>
        } @else if (estado.conflito(); as c) {
          <div class="caixa alerta" role="alert">
            <div class="alerta-titulo">
              <span class="icone-alerta" aria-hidden="true">!</span>
              <h1 #titulo tabindex="-1" class="texto-alerta">Este horário acabou de ser reservado</h1>
            </div>
            @if (c.alternativas.length) {
              <p class="nota escura">Escolha outro horário disponível:</p>
              <div class="horarios">
                @for (h of c.alternativas; track h) {
                  <button type="button" class="horario" (click)="escolherAlternativa(h)">
                    <b>{{ h }}</b><span>Disponível</span>
                  </button>
                }
              </div>
            } @else {
              <p class="nota escura">Não há mais horários livres neste dia. Escolha outro dia.</p>
            }
          </div>
          <a class="botao secundario" routerLink="/horario">Voltar</a>
        }
      </main>
      <footer class="rodape">
        <button type="button" class="botao" (click)="novo()">Fazer novo agendamento</button>
      </footer>
    </div>
  `,
})
export class Resultado implements OnInit, AfterViewInit {
  private readonly router = inject(Router);
  readonly estado = inject(AgendamentoEstado);
  private readonly titulo = viewChild<ElementRef<HTMLElement>>('titulo');

  ngOnInit(): void {
    if (!this.estado.confirmado() && !this.estado.conflito()) this.router.navigate(['/']);
  }

  ngAfterViewInit(): void {
    // Leva o foco ao título para que leitores de tela anunciem o resultado.
    this.titulo()?.nativeElement.focus();
  }

  extenso(iso: string): string {
    return dataPorExtenso(iso);
  }

  escolherAlternativa(hora: string): void {
    this.estado.hora.set(hora);
    this.estado.limparResultado();
    this.router.navigate(['/horario']);
  }

  novo(): void {
    this.estado.reiniciar();
    this.router.navigate(['/']);
  }
}
