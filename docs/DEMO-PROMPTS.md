# 🎯 Prompts de Demonstração

Use estes prompts para demonstrar as capacidades do Agente Fiscal Inteligente.

---

## 1. NCM Incorreto (Cerveja vs Refrigerante)

```
Analise este item de NFe:
- Produto: CERVEJA PILSEN LATA 350ML
- NCM: 22021000
- CFOP: 5102
- CST: 00
- Emitente CRT: 3 (Regime Normal)
```

**Resultado esperado:** Erro crítico - NCM de refrigerante usado para cerveja.

---

## 2. CST vs CSOSN (Simples Nacional)

```
Analise este item:
- Produto: Notebook Dell Inspiron
- NCM: 84713000
- CFOP: 6102
- CST: 00
- Emitente CRT: 1 (Simples Nacional)
- UF Origem: SP, UF Destino: RJ
```

**Resultado esperado:** Erro - Simples Nacional deve usar CSOSN, não CST.

---

## 3. Alíquota Interestadual Errada (Produto Importado)

```
Analise:
- Produto: Whisky Escocês 12 anos
- NCM: 22083000
- Origem: 1 (Importado)
- Operação: Interestadual (SP -> RJ)
- Alíquota ICMS informada: 12%
```

**Resultado esperado:** Erro - Deveria ser 4% (Resolução SF 13/2012).

---

## 4. Consulta de NCM com IPI

```
Consulte o NCM 22030000 e me diga qual a alíquota de IPI para cerveja.
```

**Resultado esperado:** NCM 22030000 - Cervejas de malte | IPI: 6%

---

## 5. Validação de CFOP

```
O CFOP 5102 está correto para uma empresa que fabrica os próprios produtos e está vendendo internamente?
```

**Resultado esperado:** Não - 5102 é para revenda. Fabricante deve usar 5101.

---

## 6. Origem e Alíquota Interestadual

```
Valide: produto com origem 0 (nacional) em operação de MG para BA. Qual a alíquota correta?
```

**Resultado esperado:** 7% (Sul/Sudeste para Norte/Nordeste).

---

## 7. Análise Completa de NFe

```
Analise esta NFe completa:

Emitente:
- CNPJ: 12.345.678/0001-90
- CRT: 1 (Simples Nacional)
- UF: SP

Destinatário:
- CNPJ: 98.765.432/0001-10
- UF: RJ

Item 1:
- Produto: Smartphone Samsung Galaxy
- NCM: 85171200
- CFOP: 6102
- CST: 00
- Origem: 1 (Importado)
- Alíquota ICMS: 12%

Item 2:
- Produto: Cabo USB-C
- NCM: 85444200
- CFOP: 6102
- CSOSN: 102
- Origem: 0 (Nacional)
```

**Resultado esperado:** Múltiplos erros - CST em empresa Simples, alíquota errada para importado, inconsistência entre itens.

---

## 8. CEST Obrigatório

```
Preciso de CEST para vender cigarros? Qual seria o código?
```

**Resultado esperado:** Sim, cigarros (NCM 2402) exigem CEST. Código: 04.001.00.

---

## 9. Operação de Devolução

```
Uma empresa está fazendo devolução de compra. Ela recebeu com CFOP 1102. Qual CFOP deve usar na devolução?
```

**Resultado esperado:** CFOP 5202 (Devolução de compra para comercialização).

---

## 10. Substituição Tributária

```
Analise:
- Produto: Cerveja 600ml
- NCM: 22030000
- CST: 00 (Tributado integralmente)
- Operação: Venda para consumidor final em SP

O CST está correto ou deveria ser 60 (ST já recolhida)?
```

**Resultado esperado:** Se cerveja em SP, geralmente está em regime de ST. CST 60 seria mais adequado se o ICMS-ST já foi recolhido anteriormente.

---

## 11. Comparação de Regimes

```
Qual a diferença entre CST 00 e CSOSN 101? Quando usar cada um?
```

**Resultado esperado:** Explicação sobre regime normal (CST) vs Simples Nacional (CSOSN).

---

## 12. Consulta de CFOP por Tipo de Operação

```
Quais CFOPs devo usar para:
1. Venda interna de produção própria
2. Venda interestadual de mercadoria de terceiros
3. Exportação
```

**Resultado esperado:** 5101, 6102, 7101.

---

## Dicas para Demonstração

1. **Comece simples** - Use os prompts 1-3 primeiro
2. **Mostre as tools** - Prompts 4 e 6 mostram as consultas à base
3. **Demonstre complexidade** - Prompt 7 mostra análise multi-item
4. **Responda dúvidas** - Prompts 11-12 mostram capacidade consultiva

---

*Agente Fiscal Inteligente - Demonstração*
