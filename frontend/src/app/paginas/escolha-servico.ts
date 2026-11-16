import { Component, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { forkJoin } from 'rxjs';

import { AgendamentoEstado } from '../core/agendamento-estado.service';
import { ApiService } from '../core/api.service';
import { Profissional, Servico } from '../core/modelos';
import { Cabecalho } from '../shared/cabecalho';

/** Tela 1 — Entrada principal: escolha de serviço e profissional (RF01, RNF04). */
@Component({
  selector: 'app-escolha-servico',
  imports: [Cabecalho],
  template: `
    <div class="tela">
      <app-cabecalho [passo]="1" />
      <main>
        @if (erro()) {
          <p class="alerta-erro" role="alert"><span class="ico" aria-hidden="true">!</span>{{ erro() }}</p>
        }
        <h1 class="titulo-secao">1. Escolha o serviço</h1>
        <div role="group" aria-label="Serviços">
          @for (s of servicos(); track s.id) {
            <button type="button" class="cartao" [class.sel]="estado.servico()?.id === s.id"
                    [attr.aria-pressed]="estado.servico()?.id === s.id" (click)="estado.servico.set(s)">
              <span>
                <span class="t">{{ s.nome }}</span>
                <span class="d">{{ s.duracao_minutos }} min · {{ preco(s.preco) }}</span>
              </span>
              @if (estado.servico()?.id === s.id) {
                <span class="tag"><span class="chk" aria-hidden="true">✓</span>Selecionado</span>
              }
            </button>
          }
        </div>

        <h2 class="titulo-secao">2. Escolha a profissional</h2>
        <div class="grade-2" role="group" aria-label="Profissionais">
          @for (p of profissionais(); track p.id) {
            <button type="button" class="opcao" [class.sel]="!estado.semPreferencia() && estado.profissional()?.id === p.id"
                    [attr.aria-pressed]="!estado.semPreferencia() && estado.profissional()?.id === p.id"
                    (click)="escolher(p)">
              @if (!estado.semPreferencia() && estado.profissional()?.id === p.id) {
                <span class="chk" aria-hidden="true">✓</span>
              }
              {{ p.nome }}
            </button>
          }
        </div>
        <button type="button" class="opcao largura-total" [class.sel]="estado.semPreferencia()"
                [attr.aria-pressed]="estado.semPreferencia()" (click)="semPreferencia()">
          @if (estado.semPreferencia()) { <span class="chk" aria-hidden="true">✓</span> }
          Sem preferência
        </button>
      </main>
      <footer class="rodape">
        <button type="button" class="botao" [disabled]="!podeContinuar()" (click)="continuar()">Continuar</button>
        @if (!podeContinuar()) {
          <p class="dica">Escolha um serviço e uma profissional para continuar.</p>
        }
      </footer>
    </div>
  `,
})
export class EscolhaServico implements OnInit {
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);
  readonly estado = inject(AgendamentoEstado);
  readonly servicos = signal<Servico[]>([]);
  readonly profissionais = signal<Profissional[]>([]);
  readonly erro = signal<string | null>(null);

  ngOnInit(): void {
    forkJoin([this.api.servicos(), this.api.profissionais()]).subscribe({
      next: ([servicos, profissionais]) => {
        this.servicos.set(servicos);
        this.profissionais.set(profissionais);
      },
      error: () => this.erro.set('Não foi possível carregar os serviços. Verifique sua conexão e tente novamente.'),
    });
  }

  escolher(p: Profissional): void {
    this.estado.semPreferencia.set(false);
    this.estado.profissional.set(p);
  }

  semPreferencia(): void {
    this.estado.semPreferencia.set(true);
    this.estado.profissional.set(null);
  }

  podeContinuar(): boolean {
    return !!this.estado.servico() && (this.estado.semPreferencia() || !!this.estado.profissional());
  }

  continuar(): void {
    this.estado.hora.set(null);
    this.estado.limparResultado();
    this.router.navigate(['/horario']);
  }

  preco(valor: number): string {
    return valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  }
}
