import { Injectable, signal } from '@angular/core';

import { AgendamentoConfirmado, Conflito, Profissional, Servico } from './modelos';

/** Estado do fluxo de agendamento compartilhado entre as três telas. */
@Injectable({ providedIn: 'root' })
export class AgendamentoEstado {
  readonly servico = signal<Servico | null>(null);
  /** null = "Sem preferência" (qualquer profissional com horário livre). */
  readonly profissional = signal<Profissional | null>(null);
  readonly semPreferencia = signal(false);
  readonly data = signal<string | null>(null);
  readonly hora = signal<string | null>(null);
  readonly nome = signal('');
  readonly telefone = signal('');
  readonly confirmado = signal<AgendamentoConfirmado | null>(null);
  readonly conflito = signal<Conflito | null>(null);

  limparResultado(): void {
    this.confirmado.set(null);
    this.conflito.set(null);
  }

  reiniciar(): void {
    this.servico.set(null);
    this.profissional.set(null);
    this.semPreferencia.set(false);
    this.data.set(null);
    this.hora.set(null);
    this.limparResultado();
  }
}
