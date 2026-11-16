import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { Router } from '@angular/router';

import { ApiService } from '../core/api.service';
import { AuthService } from '../core/auth.service';
import { Cabecalho } from '../shared/cabecalho';

/** Login da equipe (RF03). */
@Component({
  selector: 'app-painel-login',
  imports: [Cabecalho],
  template: `
    <div class="tela">
      <app-cabecalho subtitulo="Área da equipe" />
      <main>
        <h1 class="titulo-secao">Entrar no painel</h1>
        <form (submit)="entrar($event)" novalidate>
          <label for="email">E-mail</label>
          <input id="email" class="campo" type="email" autocomplete="username" required
                 [value]="email()" (input)="email.set($any($event.target).value)" />

          <label for="senha">Senha</label>
          <input id="senha" class="campo" type="password" autocomplete="current-password" required
                 [value]="senha()" (input)="senha.set($any($event.target).value)" />

          @if (erro()) {
            <p class="msg-erro" role="alert"><span class="ico" aria-hidden="true">!</span>{{ erro() }}</p>
          }
          <button type="submit" class="botao espaco-topo" [disabled]="enviando()">
            {{ enviando() ? 'Entrando…' : 'Entrar' }}
          </button>
        </form>
      </main>
    </div>
  `,
})
export class PainelLogin {
  private readonly api = inject(ApiService);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  readonly email = signal('');
  readonly senha = signal('');
  readonly erro = signal<string | null>(null);
  readonly enviando = signal(false);

  entrar(evento: Event): void {
    evento.preventDefault();
    if (!this.email() || !this.senha()) {
      this.erro.set('Informe e-mail e senha.');
      return;
    }
    this.enviando.set(true);
    this.erro.set(null);
    this.api.login(this.email(), this.senha()).subscribe({
      next: (sessao) => {
        this.auth.entrar(sessao);
        this.router.navigate(['/equipe/agenda']);
      },
      error: (e: HttpErrorResponse) => {
        this.enviando.set(false);
        this.erro.set(
          e.status === 401 || e.status === 429
            ? e.error?.detail
            : 'Não foi possível entrar agora. Tente novamente em instantes.',
        );
      },
    });
  }
}
