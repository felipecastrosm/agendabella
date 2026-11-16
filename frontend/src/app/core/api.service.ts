import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import {
  Agenda,
  AgendamentoConfirmado,
  AgendamentoPainel,
  Horarios,
  NovoAgendamento,
  Profissional,
  Servico,
  Sessao,
} from './modelos';

/** Único ponto de comunicação com a API (HTTPS + JSON). */
@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/api`;

  servicos(): Observable<Servico[]> {
    return this.http.get<Servico[]>(`${this.base}/servicos`);
  }

  profissionais(): Observable<Profissional[]> {
    return this.http.get<Profissional[]>(`${this.base}/profissionais`);
  }

  horarios(idServico: number, idProfissional: number, data: string): Observable<Horarios> {
    const params = new HttpParams()
      .set('id_servico', idServico)
      .set('id_profissional', idProfissional)
      .set('data', data);
    return this.http.get<Horarios>(`${this.base}/horarios-disponiveis`, { params });
  }

  agendar(dados: NovoAgendamento): Observable<AgendamentoConfirmado> {
    return this.http.post<AgendamentoConfirmado>(`${this.base}/agendamentos`, dados);
  }

  login(email: string, senha: string): Observable<Sessao> {
    return this.http.post<Sessao>(`${this.base}/auth/login`, { email, senha });
  }

  agenda(data: string, dias: number): Observable<Agenda> {
    const params = new HttpParams().set('data', data).set('dias', dias);
    return this.http.get<Agenda>(`${this.base}/painel/agenda`, { params });
  }

  alterarStatus(id: number, status: string): Observable<AgendamentoPainel> {
    return this.http.patch<AgendamentoPainel>(`${this.base}/painel/agendamentos/${id}`, { status });
  }
}
