export interface Servico {
  id: number;
  nome: string;
  duracao_minutos: number;
  preco: number;
}

export interface Profissional {
  id: number;
  nome: string;
}

export interface Horarios {
  data: string;
  id_profissional: number;
  id_servico: number;
  horarios: string[];
}

export interface NovoAgendamento {
  id_servico: number;
  id_profissional: number;
  data: string;
  hora_inicio: string;
  nome: string;
  telefone: string;
}

export interface AgendamentoConfirmado {
  id: number;
  servico: string;
  profissional: string;
  data: string;
  hora_inicio: string;
  hora_fim: string;
  status: string;
}

export interface Conflito {
  mensagem: string;
  alternativas: string[];
}

export interface Sessao {
  access_token: string;
  nome: string;
  papel: string;
}

export interface AgendamentoPainel {
  id: number;
  data: string;
  hora_inicio: string;
  hora_fim: string;
  status: 'confirmado' | 'realizado' | 'falta' | 'cancelado';
  cliente: string;
  telefone: string;
  servico: string;
  id_profissional: number;
  profissional: string;
}

export interface Agenda {
  inicio: string;
  fim: string;
  profissionais: { id_profissional: number; profissional: string; agendamentos: AgendamentoPainel[] }[];
}
