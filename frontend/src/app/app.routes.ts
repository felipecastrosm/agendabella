import { Routes } from '@angular/router';

import { exigeLogin } from './core/auth.service';
import { EscolhaHorario } from './paginas/escolha-horario';
import { EscolhaServico } from './paginas/escolha-servico';
import { PainelAgenda } from './paginas/painel-agenda';
import { PainelLogin } from './paginas/painel-login';
import { Resultado } from './paginas/resultado';

export const routes: Routes = [
  { path: '', component: EscolhaServico, title: 'Agende seu horário | Studio Bella Cabelos' },
  { path: 'horario', component: EscolhaHorario, title: 'Escolha o horário | Studio Bella Cabelos' },
  { path: 'resultado', component: Resultado, title: 'Resultado do agendamento | Studio Bella Cabelos' },
  { path: 'equipe', component: PainelLogin, title: 'Área da equipe | AgendaBella' },
  { path: 'equipe/agenda', component: PainelAgenda, canActivate: [exigeLogin], title: 'Agenda | AgendaBella' },
  { path: '**', redirectTo: '' },
];
