import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { forkJoin, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

import { AgendamentoEstado } from '../core/agendamento-estado.service';
import { ApiService } from '../core/api.service';
import { dataCurta, proximosDias } from '../core/datas';
import { Conflito, Profissional } from '../core/modelos';
import { mascararTelefone, validarNome, validarTelefone } from '../core/telefone';
import { Cabecalho } from '../shared/cabecalho';

/** Tela 2 — Funcionalidade central: escolha de horário e dados da cliente (RF01, RF02, RNF02, RNF04). */
@Component({
  selector: 'app-escolha-horario',
  imports: [Cabecalho, RouterLink],
  template: `
    <div class="tela">
      <app-cabecalho [passo]="2" />
      <main>
        <div class="resumo">
          <div><b>{{ estado.servico()?.nome }}</b> com <b>{{ nomeProfissional() }}</b> · {{ estado.servico()?.duracao_minutos }} min</div>
          <a routerLink="/">Alterar</a>
        </div>

        <h1 class="titulo-secao">Escolha o dia</h1>
        <div class="dias" role="group" aria-label="Dias disponíveis">
          @for (d of dias; track d.iso) {
            <button type="button" class="dia" [class.sel]="estado.data() === d.iso"
                    [attr.aria-pressed]="estado.data() === d.iso" (click)="escolherDia(d.iso)">
              {{ d.semana }}<b>{{ d.numero }}</b>
            </button>
          }
        </div>

        <h2 class="titulo-secao">Horários disponíveis — {{ dataSelecionada() }}</h2>
        @if (carregando()) {
          <p class="dica" role="status">Carregando horários…</p>
        } @else if (horarios().length === 0) {
          <p class="vazio" role="status">
            Não há horários livres neste dia: o salão pode estar fechado ou com a agenda completa. Escolha outro dia.
          </p>
        } @else {
          @for (periodo of periodos(); track periodo.nome) {
            @if (periodo.horarios.length) {
              <h3 class="periodo">{{ periodo.nome }}</h3>
              <div class="horarios" role="group" [attr.aria-label]="'Horários disponíveis — ' + periodo.nome">
                @for (h of periodo.horarios; track h) {
                  <button type="button" class="horario" [class.sel]="estado.hora() === h"
                          [attr.aria-pressed]="estado.hora() === h" (click)="estado.hora.set(h)">
                    <b>@if (estado.hora() === h) { ✓ }{{ h }}</b>
                    <span>{{ estado.hora() === h ? 'Selecionado' : 'Disponível' }}</span>
                  </button>
                }
              </div>
            }
          }
        }

        <label for="nome">Seu nome</label>
        <input id="nome" class="campo" [class.invalido]="erroNome()" autocomplete="name" maxlength="80"
               [value]="estado.nome()" (input)="estado.nome.set($any($event.target).value)"
               [attr.aria-invalid]="!!erroNome()" aria-describedby="erro-nome" />
        @if (erroNome()) {
          <p class="msg-erro" id="erro-nome" role="alert"><span class="ico" aria-hidden="true">!</span>{{ erroNome() }}</p>
        }

        <label for="telefone">Telefone com DDD <span class="exemplo">— ex.: 21 90000-0000</span></label>
        <input id="telefone" class="campo" [class.invalido]="erroTelefone()" type="tel" inputmode="numeric"
               autocomplete="tel-national" [value]="estado.telefone()" (input)="digitarTelefone($event)"
               [attr.aria-invalid]="!!erroTelefone()" aria-describedby="erro-telefone" />
        @if (erroTelefone()) {
          <p class="msg-erro" id="erro-telefone" role="alert"><span class="ico" aria-hidden="true">!</span>{{ erroTelefone() }}</p>
        }
        @if (erroGeral()) {
          <p class="alerta-erro" role="alert"><span class="ico" aria-hidden="true">!</span>{{ erroGeral() }}</p>
        }
      </main>
      <footer class="rodape">
        <button type="button" class="botao" [disabled]="enviando()" (click)="confirmar()">
          {{ enviando() ? 'Confirmando…' : 'Confirmar agendamento' }}
        </button>
        <a class="botao secundario" routerLink="/">Voltar</a>
      </footer>
    </div>
  `,
})
export class EscolhaHorario implements OnInit {
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);
  readonly estado = inject(AgendamentoEstado);

  readonly dias = proximosDias(7);
  readonly horarios = signal<string[]>([]);
  readonly carregando = signal(false);
  readonly enviando = signal(false);
  readonly erroNome = signal<string | null>(null);
  readonly erroTelefone = signal<string | null>(null);
  readonly erroGeral = signal<string | null>(null);
  /** Com "Sem preferência": horário → profissionais livres nesse horário. */
  private livresPorHorario = new Map<string, number[]>();
  private profissionais: Profissional[] = [];

  readonly nomeProfissional = computed(() =>
    this.estado.semPreferencia() ? 'qualquer profissional' : this.estado.profissional()?.nome ?? '',
  );
  readonly dataSelecionada = computed(() => (this.estado.data() ? dataCurta(this.estado.data()!) : ''));
  /** Ajuste da 1ª validação: separa a lista em Manhã e Tarde para reduzir a rolagem. */
  readonly periodos = computed(() => [
    { nome: 'Manhã', horarios: this.horarios().filter((h) => h < '12:00') },
    { nome: 'Tarde', horarios: this.horarios().filter((h) => h >= '12:00') },
  ]);

  ngOnInit(): void {
    if (!this.estado.servico()) {
      this.router.navigate(['/']);
      return;
    }
    this.api.profissionais().subscribe((lista) => {
      this.profissionais = lista;
      if (this.estado.data()) {
        this.escolherDia(this.estado.data()!, true);
      } else {
        this.abrirNoPrimeiroDiaDisponivel();
      }
    });
  }

  /** Ajuste da 1ª validação: em vez de abrir em um dia fechado, abre no primeiro dia com horário livre. */
  private abrirNoPrimeiroDiaDisponivel(): void {
    const servico = this.estado.servico()!;
    const alvo = this.estado.semPreferencia() ? this.profissionais : [this.estado.profissional()!];
    this.carregando.set(true);
    forkJoin(
      alvo.map((p) =>
        this.api.proximoDia(servico.id, p.id, this.dias[0].iso).pipe(catchError(() => of({ data: null }))),
      ),
    ).subscribe((respostas) => {
      const datas = respostas.map((r) => r.data).filter((d): d is string => !!d && this.dias.some((x) => x.iso === d));
      this.escolherDia(datas.sort()[0] ?? this.dias[0].iso);
    });
  }

  escolherDia(iso: string, manterHora = false): void {
    this.estado.data.set(iso);
    if (!manterHora) this.estado.hora.set(null);
    const servico = this.estado.servico()!;
    const alvo = this.estado.semPreferencia()
      ? this.profissionais
      : [this.estado.profissional()!];
    this.carregando.set(true);
    forkJoin(
      alvo.map((p) =>
        this.api.horarios(servico.id, p.id, iso).pipe(
          map((r) => ({ id: p.id, horarios: r.horarios })),
          catchError(() => of({ id: p.id, horarios: [] as string[] })),
        ),
      ),
    ).subscribe((resultados) => {
      this.livresPorHorario = new Map();
      for (const r of resultados) {
        for (const h of r.horarios) {
          this.livresPorHorario.set(h, [...(this.livresPorHorario.get(h) ?? []), r.id]);
        }
      }
      this.horarios.set([...this.livresPorHorario.keys()].sort());
      if (this.estado.hora() && !this.livresPorHorario.has(this.estado.hora()!)) {
        this.estado.hora.set(null);
      }
      this.carregando.set(false);
    });
  }

  digitarTelefone(evento: Event): void {
    const campo = evento.target as HTMLInputElement;
    campo.value = mascararTelefone(campo.value);
    this.estado.telefone.set(campo.value);
    if (this.erroTelefone()) this.erroTelefone.set(validarTelefone(campo.value));
  }

  confirmar(): void {
    this.erroGeral.set(null);
    this.erroNome.set(validarNome(this.estado.nome()));
    this.erroTelefone.set(validarTelefone(this.estado.telefone()));
    if (!this.estado.hora()) {
      this.erroGeral.set('Escolha um horário disponível antes de confirmar.');
      return;
    }
    if (this.erroNome() || this.erroTelefone()) return;

    const hora = this.estado.hora()!;
    const idProfissional = this.estado.semPreferencia()
      ? this.livresPorHorario.get(hora)![0]
      : this.estado.profissional()!.id;

    this.enviando.set(true);
    this.api
      .agendar({
        id_servico: this.estado.servico()!.id,
        id_profissional: idProfissional,
        data: this.estado.data()!,
        hora_inicio: hora,
        nome: this.estado.nome().trim(),
        telefone: this.estado.telefone(),
      })
      .subscribe({
        next: (confirmado) => {
          this.estado.confirmado.set(confirmado);
          this.estado.conflito.set(null);
          this.router.navigate(['/resultado']);
        },
        error: (erro: HttpErrorResponse) => {
          this.enviando.set(false);
          if (erro.status === 409) {
            this.estado.conflito.set(erro.error as Conflito);
            this.estado.confirmado.set(null);
            this.router.navigate(['/resultado']);
          } else if (erro.status === 422) {
            const msg = (erro.error?.detail ?? [])[0] ?? 'Verifique os dados informados.';
            if (String(msg).toLowerCase().includes('telefone')) this.erroTelefone.set(msg);
            else if (String(msg).toLowerCase().includes('nome')) this.erroNome.set(msg);
            else this.erroGeral.set(msg);
          } else {
            this.erroGeral.set('Não foi possível concluir o agendamento agora. Tente novamente em instantes.');
          }
        },
      });
  }
}
