import { HttpInterceptorFn } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { Sessao } from './modelos';

const CHAVE = 'agendabella.sessao';

/** Sessão da equipe guardada apenas na aba atual (sessionStorage) e removida no logout. */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly sessao = signal<Sessao | null>(this.ler());
  readonly logada = computed(() => this.sessao() !== null);
  readonly nome = computed(() => this.sessao()?.nome ?? '');
  readonly token = computed(() => this.sessao()?.access_token ?? null);

  entrar(sessao: Sessao): void {
    sessionStorage.setItem(CHAVE, JSON.stringify(sessao));
    this.sessao.set(sessao);
  }

  sair(): void {
    sessionStorage.removeItem(CHAVE);
    this.sessao.set(null);
  }

  private ler(): Sessao | null {
    try {
      const bruto = sessionStorage.getItem(CHAVE);
      return bruto ? (JSON.parse(bruto) as Sessao) : null;
    } catch {
      return null;
    }
  }
}

/** Anexa o token somente às chamadas do painel. */
export const tokenInterceptor: HttpInterceptorFn = (req, next) => {
  const token = inject(AuthService).token();
  if (token && req.url.includes('/api/painel/')) {
    req = req.clone({ setHeaders: { Authorization: `Bearer ${token}` } });
  }
  return next(req);
};

export const exigeLogin: CanActivateFn = () => {
  const auth = inject(AuthService);
  return auth.logada() ? true : inject(Router).parseUrl('/equipe');
};
