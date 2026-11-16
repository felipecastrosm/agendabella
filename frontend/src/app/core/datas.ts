const DIAS = ['dom', 'seg', 'ter', 'qua', 'qui', 'sex', 'sáb'];
const DIAS_LONGOS = ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado'];

/** Data local no formato AAAA-MM-DD (sem conversão para UTC). */
export function isoLocal(d: Date): string {
  const mes = String(d.getMonth() + 1).padStart(2, '0');
  const dia = String(d.getDate()).padStart(2, '0');
  return `${d.getFullYear()}-${mes}-${dia}`;
}

export function deIso(iso: string): Date {
  const [a, m, d] = iso.split('-').map(Number);
  return new Date(a, m - 1, d);
}

export function proximosDias(qtd: number, inicio = new Date()): { iso: string; semana: string; numero: number }[] {
  return Array.from({ length: qtd }, (_, i) => {
    const d = new Date(inicio.getFullYear(), inicio.getMonth(), inicio.getDate() + i);
    return { iso: isoLocal(d), semana: DIAS[d.getDay()], numero: d.getDate() };
  });
}

/** "Terça, 24/11" */
export function dataPorExtenso(iso: string): string {
  const d = deIso(iso);
  return `${DIAS_LONGOS[d.getDay()]}, ${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}`;
}

/** "ter, 24/11" */
export function dataCurta(iso: string): string {
  const d = deIso(iso);
  return `${DIAS[d.getDay()]}, ${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}`;
}
