# 🎯 Prompts de Demonstração

Use estes prompts para demonstrar o fluxo oficial do AgentOS com NFe automática.

---

## 1. Fluxo principal: upload de XML

```
Anexei uma NFe em XML. Faça a auditoria fiscal completa.
```

**Resultado esperado:** O agente deve carregar o XML, auditar automaticamente e responder com resumo executivo e inconsistências.

---

## 2. Fluxo principal com instrução curta

```
Segue a nota. Me diga o que está errado e o que eu deveria corrigir.
```

**Resultado esperado:** O agente deve analisar a nota anexada sem exigir prompt detalhado.

---

## 3. XML colado na conversa

```
Analise este XML de NFe e faça a auditoria completa:

<cole aqui o XML bruto da nota>
```

**Resultado esperado:** O agente deve tratar o XML colado como entrada válida e devolver a auditoria.

---

## 4. Follow-up após a auditoria

```
Qual item dessa nota teve maior risco fiscal?
```

**Resultado esperado:** O agente deve usar a nota já carregada na sessão.

---

## 5. Follow-up orientado a correção

```
Me dê as correções sugeridas campo por campo para essa nota.
```

**Resultado esperado:** O agente deve responder com sugestões estruturadas de correção.

---

## 6. Pedir o resultado estruturado

```
Agora me mostre o resultado estruturado completo da auditoria em JSON.
```

**Resultado esperado:** O agente deve retornar o JSON completo da auditoria atual.

---

## 7. Consulta fiscal sem nota anexada

```
O CFOP 5102 está correto para uma empresa que fabrica os próprios produtos e está vendendo internamente?
```

**Resultado esperado:** O agente continua respondendo perguntas fiscais consultivas usando as tools.

---

## 8. Entrada inválida

```
Anexei um PDF da DANFE. Analise essa nota.
```

**Resultado esperado:** O agente deve informar com clareza que esta etapa suporta XML de NFe, não PDF/imagem.

---

## Dicas para Demonstração

1. **Comece pelo upload de XML** - Esse é o fluxo principal do produto.
2. **Use XML colado como fallback** - Valida a segunda forma oficial de entrada.
3. **Faça follow-ups** - Confirma se a sessão está preservando a nota atual.
4. **Teste erro de entrada** - PDF ou múltiplos arquivos devem ser rejeitados com clareza.

---

*Agente Fiscal Inteligente - Demonstração*
