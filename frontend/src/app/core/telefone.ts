/** Mesma regra do servidor: DDD válido + 10 ou 11 dígitos. Retorna mensagem de erro ou null. */
export function validarTelefone(valor: string): string | null {
  const digitos = valor.replace(/[\s()\-]/g, '');
  if (!/^\d{10,11}$/.test(digitos)) {
    return 'Telefone incompleto. Informe o telefone com DDD, ex.: 21 90000-0000.';
  }
  const ddd = Number(digitos.slice(0, 2));
  if (ddd < 11) {
    return 'DDD inválido. Informe o telefone com DDD, ex.: 21 90000-0000.';
  }
  return null;
}

export function validarNome(valor: string): string | null {
  const limpo = valor.trim().replace(/\s+/g, ' ');
  return /^[A-Za-zÀ-ÖØ-öø-ÿ' -]{2,80}$/.test(limpo)
    ? null
    : 'Informe seu nome usando apenas letras (mínimo de 2 caracteres).';
}

/** Aplica a máscara "21 90000-0000" enquanto a pessoa digita. */
export function mascararTelefone(valor: string): string {
  const d = valor.replace(/\D/g, '').slice(0, 11);
  if (d.length <= 2) return d;
  const resto = d.slice(2);
  const corte = resto.length > 8 ? 5 : 4;
  return resto.length > corte ? `${d.slice(0, 2)} ${resto.slice(0, corte)}-${resto.slice(corte)}` : `${d.slice(0, 2)} ${resto}`;
}
