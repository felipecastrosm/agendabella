import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';

import { ApiService } from '../core/api.service';
import { AuthService } from '../core/auth.service';
import { dataCurta, isoLocal } from '../core/datas';
import { Agenda, AgendamentoPainel } from '../core/modelos';
import { Cabecalho } from '../shared/cabecalho';

const ROTULOS: Record<AgendamentoPainel['status'], { texto: string; icone: string }> = {
  confirmado: { texto: 'Confirmado', icone: '●' },
  realizado: { texto: 'Realizado', icone: '✓' },
  falta: { texto: 'Falta', icone: '✕' },
  cancelado: { texto: 'Cancelado', icone: '⊘' },
};

/** Painel da equipe: agenda do dia/semana por profissional e alteração de status (RF04, RF05). */
@Component({
  selector: 'app-painel-agenda',
  imports: [Cabecalho],
  template: `
    <div class="tela">
      <app-cabecalho subtitulo="Agenda da equipe" />
      <main>
        <div class="barra-painel">
          <span>Olá, <b>{{ auth.nome() }}</b></span>
          <button type="button" class="link" (click)="sair()">Sair</button>
        </div>

        <label for="data">Dia</label>
        <input id="data" class="campo" type="date" [value]="data()" (change)="mudarData($any($event.target).value)" />

        <div class="alternador" role="group" aria-label="Período">
          <button type="button" class="opcao" [class.sel]="dias() === 1" [attr.aria-pressed]="dias() === 1" (click)="mudarDias(1)">Dia</button>
          <button type="button" class="opcao" [class.sel]="dias() === 7" [attr.aria-pressed]="dias() === 7" (click)="mudarDias(7)">Semana</button>
        </div>

        @if (mensagem()) {
          <p class="alerta-erro" role="alert"><span class="ico" aria-hidden="true">!</span>{{ mensagem() }}</p>
        }

        @for (grupo of agenda()?.profissionais ?? []; track grupo.id_profissional) {
          <section class="grupo">
            <h2 class="titulo-secao">{{ grupo.profissional }}</h2>
            @if (grupo.agendamentos.length === 0) {
              <p class="vazio">Nenhum agendamento no período.</p>
            }
            @for (ag of grupo.agendamentos; track ag.id) {
              <article class="item" [class.cancelado]="ag.status === 'cancelado'">
                <div class="item-topo">
                  <b>{{ dias() === 7 ? curta(ag.data) + ' · ' : '' }}{{ ag.hora_inicio }} às {{ ag.hora_fim }}</b>
                  <span class="status status-{{ ag.status }}">
                    <span aria-hidden="true">{{ rotulo(ag).icone }}</span> {{ rotulo(ag).texto }}
                  </span>
                </div>
                <div>{{ ag.cliente }} · {{ ag.servico }}</div>
                <div class="nota">Tel.: {{ ag.telefone }}</div>
                @if (ag.status === 'confirmado') {
                  <div class="acoes">
                    <button type="button" class="opcao" [disabled]="futuro(ag)" (click)="alterar(ag, 'realizado')">✓ Realizado</button>
                    <button type="button" class="opcao" [disabled]="futuro(ag)" (click)="alterar(ag, 'falta')">✕ Falta</button>
                    <button type="button" class="opcao" (click)="alterar(ag, 'cancelado')">Cancelar</button>
                  </div>
                  @if (futuro(ag)) {
                    <p class="dica esquerda">Realizado e falta ficam disponíveis a partir do horário marcado.</p>
                  }
                }
              </article>
            }
          </section>
        }
      </main>
    </div>
  `,
})
export class PainelAgenda implements OnInit {
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);
  readonly auth = inject(AuthService);
  readonly data = signal(isoLocal(new Date()));
  readonly dias = signal(1);
  readonly agenda = signal<Agenda | null>(null);
  readonly mensagem = signal<string | null>(null);

  ngOnInit(): void {
    this.carregar();
  }

  carregar(): void {
    this.api.agenda(this.data(), this.dias()).subscribe({
      next: (a) => this.agenda.set(a),
      error: (e: HttpErrorResponse) => this.tratarErro(e),
    });
  }

  mudarData(valor: string): void {
    if (!valor) return;
    this.data.set(valor);
    this.carregar();
  }

  mudarDias(qtd: number): void {
    this.dias.set(qtd);
    this.carregar();
  }

  futuro(ag: AgendamentoPainel): boolean {
    return new Date(`${ag.data}T${ag.hora_inicio}:00`) > new Date();
  }

  alterar(ag: AgendamentoPainel, status: string): void {
    if (status === 'cancelado' && !confirmarCancelamento(ag)) return;
    this.mensagem.set(null);
    this.api.alterarStatus(ag.id, status).subscribe({
      next: () => this.carregar(),
      error: (e: HttpErrorResponse) => this.tratarErro(e),
    });
  }

  rotulo(ag: AgendamentoPainel) {
    return ROTULOS[ag.status];
  }

  curta(iso: string): string {
    return dataCurta(iso);
  }

  sair(): void {
    this.auth.sair();
    this.router.navigate(['/equipe']);
  }

  private tratarErro(e: HttpErrorResponse): void {
    if (e.status === 401) {
      this.auth.sair();
      this.router.navigate(['/equipe']);
      return;
    }
    this.mensagem.set(e.error?.detail ?? 'Não foi possível atualizar a agenda. Tente novamente.');
  }
}

function confirmarCancelamento(ag: AgendamentoPainel): boolean {
  return window.confirm(`Cancelar o horário de ${ag.cliente} às ${ag.hora_inicio}? O horário ficará livre para outra cliente.`);
}
