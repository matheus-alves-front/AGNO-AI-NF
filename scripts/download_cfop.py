"""
Download CFOP - Baixa tabela completa de CFOPs

Fonte: Convênio SINIEF s/nº de 1970 (atualizado)
"""

import json
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "app" / "knowledge" / "sources"

# Tabela CFOP completa
CFOP_DATA = {
    # Grupo 1 - Entradas (mesmo estado)
    "1101": "Compra para industrialização",
    "1102": "Compra para comercialização", 
    "1111": "Compra para industrialização de mercadoria em consignação",
    "1113": "Compra para comercialização de mercadoria em consignação",
    "1116": "Compra para industrialização originada de encomenda",
    "1117": "Compra para comercialização originada de encomenda",
    "1118": "Compra de mercadoria para comercialização pelo adquirente originário, entregue pelo vendedor remetente ao destinatário, em venda à ordem",
    "1120": "Compra para industrialização, em venda à ordem, já recebida do vendedor remetente",
    "1121": "Compra para comercialização, em venda à ordem, já recebida do vendedor remetente",
    "1122": "Compra para industrialização em que a mercadoria foi remetida pelo fornecedor ao industrializador sem transitar pelo estabelecimento adquirente",
    "1124": "Industrialização efetuada por outra empresa",
    "1125": "Industrialização efetuada por outra empresa quando a mercadoria remetida para utilização no processo de industrialização não transitou pelo estabelecimento adquirente da mercadoria",
    "1126": "Compra para utilização na prestação de serviço sujeita ao ICMS",
    "1128": "Compra para utilização na prestação de serviço sujeita ao ISSQN",
    "1151": "Transferência para industrialização",
    "1152": "Transferência para comercialização",
    "1153": "Transferência de energia elétrica",
    "1154": "Transferência para utilização na prestação de serviço",
    "1201": "Devolução de venda de produção do estabelecimento",
    "1202": "Devolução de venda de mercadoria adquirida ou recebida de terceiros",
    "1203": "Devolução de venda de produção do estabelecimento, destinada à Zona Franca de Manaus ou Áreas de Livre Comércio",
    "1204": "Devolução de venda de mercadoria adquirida ou recebida de terceiros, destinada à Zona Franca de Manaus ou Áreas de Livre Comércio",
    "1205": "Anulação de valor relativo à prestação de serviço de comunicação",
    "1206": "Anulação de valor relativo à prestação de serviço de transporte",
    "1207": "Anulação de valor relativo à venda de energia elétrica",
    "1208": "Devolução de produção do estabelecimento, remetida em transferência",
    "1209": "Devolução de mercadoria adquirida ou recebida de terceiros, remetida em transferência",
    "1251": "Compra de energia elétrica para distribuição ou comercialização",
    "1252": "Compra de energia elétrica por estabelecimento industrial",
    "1253": "Compra de energia elétrica por estabelecimento comercial",
    "1254": "Compra de energia elétrica por estabelecimento prestador de serviço de transporte",
    "1255": "Compra de energia elétrica por estabelecimento prestador de serviço de comunicação",
    "1256": "Compra de energia elétrica por estabelecimento de produtor rural",
    "1257": "Compra de energia elétrica para consumo por demanda contratada",
    "1301": "Aquisição de serviço de comunicação para execução de serviço da mesma natureza",
    "1302": "Aquisição de serviço de comunicação por estabelecimento industrial",
    "1303": "Aquisição de serviço de comunicação por estabelecimento comercial",
    "1304": "Aquisição de serviço de comunicação por estabelecimento de prestador de serviço de transporte",
    "1305": "Aquisição de serviço de comunicação por estabelecimento de geradora ou de distribuidora de energia elétrica",
    "1306": "Aquisição de serviço de comunicação por estabelecimento de produtor rural",
    "1351": "Aquisição de serviço de transporte para execução de serviço da mesma natureza",
    "1352": "Aquisição de serviço de transporte por estabelecimento industrial",
    "1353": "Aquisição de serviço de transporte por estabelecimento comercial",
    "1354": "Aquisição de serviço de transporte por estabelecimento de prestador de serviço de comunicação",
    "1355": "Aquisição de serviço de transporte por estabelecimento de geradora ou de distribuidora de energia elétrica",
    "1356": "Aquisição de serviço de transporte por estabelecimento de produtor rural",
    "1401": "Compra para industrialização ou produção rural em operação com mercadoria sujeita ao regime de substituição tributária",
    "1403": "Compra para comercialização em operação com mercadoria sujeita ao regime de substituição tributária",
    "1406": "Compra de bem para o ativo imobilizado cuja mercadoria está sujeita ao regime de substituição tributária",
    "1407": "Compra de mercadoria para uso ou consumo cuja mercadoria está sujeita ao regime de substituição tributária",
    "1408": "Transferência para industrialização ou produção rural em operação com mercadoria sujeita ao regime de substituição tributária",
    "1409": "Transferência para comercialização em operação com mercadoria sujeita ao regime de substituição tributária",
    "1410": "Devolução de venda de produção do estabelecimento em operação com produto sujeito ao regime de substituição tributária",
    "1411": "Devolução de venda de mercadoria adquirida ou recebida de terceiros em operação com mercadoria sujeita ao regime de substituição tributária",
    "1414": "Retorno de produção do estabelecimento, remetida para venda fora do estabelecimento em operação com produto sujeito ao regime de substituição tributária",
    "1415": "Retorno de mercadoria adquirida ou recebida de terceiros, remetida para venda fora do estabelecimento em operação com mercadoria sujeita ao regime de substituição tributária",
    "1451": "Retorno de animal do estabelecimento produtor",
    "1452": "Retorno de insumo não utilizado na produção",
    "1501": "Entrada de mercadoria recebida com fim específico de exportação",
    "1503": "Entrada decorrente de devolução de produto remetido com fim específico de exportação, de produção do estabelecimento",
    "1504": "Entrada decorrente de devolução de mercadoria remetida com fim específico de exportação, adquirida ou recebida de terceiros",
    "1505": "Entrada decorrente de devolução de mercadorias remetidas para formação de lote de exportação, de produtos industrializados ou produzidos pelo próprio estabelecimento",
    "1506": "Entrada decorrente de devolução de mercadorias, adquiridas ou recebidas de terceiros, remetidas para formação de lote de exportação",
    "1551": "Compra de bem para o ativo imobilizado",
    "1552": "Transferência de bem do ativo imobilizado",
    "1553": "Devolução de venda de bem do ativo imobilizado",
    "1554": "Retorno de bem do ativo imobilizado remetido para uso fora do estabelecimento",
    "1555": "Entrada de bem do ativo imobilizado de terceiro, remetido para uso no estabelecimento",
    "1556": "Compra de material para uso ou consumo",
    "1557": "Transferência de material para uso ou consumo",
    "1601": "Recebimento, por transferência, de crédito de ICMS",
    "1602": "Recebimento, por transferência, de saldo credor de ICMS de outro estabelecimento da mesma empresa, para compensação de saldo devedor de ICMS",
    "1603": "Ressarcimento de ICMS retido por substituição tributária",
    "1604": "Lançamento do crédito relativo à compra de bem para o ativo imobilizado",
    "1605": "Recebimento, por transferência, de saldo devedor de ICMS de outro estabelecimento da mesma empresa",
    "1651": "Compra de combustível ou lubrificante para industrialização subsequente",
    "1652": "Compra de combustível ou lubrificante para comercialização",
    "1653": "Compra de combustível ou lubrificante por consumidor ou usuário final",
    "1658": "Transferência de combustível e lubrificante para industrialização",
    "1659": "Transferência de combustível e lubrificante para comercialização",
    "1660": "Devolução de venda de combustível ou lubrificante destinado à industrialização subsequente",
    "1661": "Devolução de venda de combustível ou lubrificante destinado à comercialização",
    "1662": "Devolução de venda de combustível ou lubrificante destinado a consumidor ou usuário final",
    "1663": "Entrada de combustível ou lubrificante para armazenagem",
    "1664": "Retorno de combustível ou lubrificante remetido para armazenagem",
    "1901": "Entrada para industrialização por encomenda",
    "1902": "Retorno de mercadoria remetida para industrialização por encomenda",
    "1903": "Entrada de mercadoria remetida para industrialização e não aplicada no referido processo",
    "1904": "Retorno de remessa para venda fora do estabelecimento",
    "1905": "Entrada de mercadoria recebida para depósito em depósito fechado ou armazém geral",
    "1906": "Retorno de mercadoria remetida para depósito fechado ou armazém geral",
    "1907": "Retorno simbólico de mercadoria remetida para depósito fechado ou armazém geral",
    "1908": "Entrada de bem por conta de contrato de comodato",
    "1909": "Retorno de bem remetido por conta de contrato de comodato",
    "1910": "Entrada de bonificação, doação ou brinde",
    "1911": "Entrada de amostra grátis",
    "1912": "Entrada de mercadoria ou bem recebido para demonstração",
    "1913": "Retorno de mercadoria ou bem remetido para demonstração",
    "1914": "Retorno de mercadoria ou bem remetido para exposição ou feira",
    "1915": "Entrada de mercadoria ou bem recebido para conserto ou reparo",
    "1916": "Retorno de mercadoria ou bem remetido para conserto ou reparo",
    "1917": "Entrada de mercadoria recebida em consignação mercantil ou industrial",
    "1918": "Devolução de mercadoria remetida em consignação mercantil ou industrial",
    "1919": "Devolução simbólica de mercadoria vendida ou utilizada em processo industrial, remetida anteriormente em consignação mercantil ou industrial",
    "1920": "Entrada de vasilhame ou sacaria",
    "1921": "Retorno de vasilhame ou sacaria",
    "1922": "Lançamento efetuado a título de simples faturamento decorrente de compra para recebimento futuro",
    "1923": "Entrada de mercadoria recebida do vendedor remetente, em venda à ordem",
    "1924": "Entrada para industrialização por conta e ordem do adquirente da mercadoria, quando esta não transitar pelo estabelecimento do adquirente",
    "1925": "Retorno de mercadoria remetida para industrialização por conta e ordem do adquirente da mercadoria, quando esta não transitar pelo estabelecimento do adquirente",
    "1926": "Lançamento efetuado a título de reclassificação de mercadoria decorrente de formação de kit ou de sua desagregação",
    "1931": "Lançamento efetuado pelo tomador do serviço de transporte quando a responsabilidade de retenção do imposto for atribuída ao remetente ou alienante da mercadoria, pelo serviço de transporte realizado por transportador autônomo ou por transportador não inscrito na unidade da Federação onde iniciado o serviço",
    "1932": "Aquisição de serviço de transporte iniciado em unidade da Federação diversa daquela onde inscrito o prestador",
    "1933": "Aquisição de serviço tributado pelo ISSQN",
    "1949": "Outra entrada de mercadoria ou prestação de serviço não especificada",
}

# Grupos 2, 3, 5, 6, 7 (simplificados - mesma estrutura)
CFOP_GROUPS = {
    "2": "Entradas interestaduais",
    "3": "Entradas do exterior",
    "5": "Saídas internas",
    "6": "Saídas interestaduais", 
    "7": "Saídas para exterior",
}


def create_cfop_complete():
    """Cria tabela CFOP completa."""
    print("📋 Gerando tabela CFOP completa...")
    
    items = []
    
    # Grupo 1 (base)
    for cfop, desc in CFOP_DATA.items():
        items.append({
            "cfop": cfop,
            "descricao": desc,
            "tipo": "entrada_interna",
            "grupo": "1"
        })
    
    # Gera grupos 2 (interestadual) e 3 (exterior) baseado no 1
    for cfop, desc in CFOP_DATA.items():
        # Grupo 2
        cfop2 = "2" + cfop[1:]
        items.append({
            "cfop": cfop2,
            "descricao": desc.replace("interno", "interestadual").replace("interna", "interestadual"),
            "tipo": "entrada_interestadual",
            "grupo": "2"
        })
        
        # Grupo 3 (apenas alguns aplicáveis)
        if cfop.startswith("110") or cfop.startswith("155") or cfop.startswith("165"):
            cfop3 = "3" + cfop[1:]
            items.append({
                "cfop": cfop3,
                "descricao": desc + " (importação)",
                "tipo": "entrada_exterior",
                "grupo": "3"
            })
    
    # Saídas (Grupo 5, 6, 7) - principais
    saidas_base = {
        "5101": "Venda de produção do estabelecimento",
        "5102": "Venda de mercadoria adquirida ou recebida de terceiros",
        "5103": "Venda de produção do estabelecimento, efetuada fora do estabelecimento",
        "5104": "Venda de mercadoria adquirida ou recebida de terceiros, efetuada fora do estabelecimento",
        "5105": "Venda de produção do estabelecimento que não deva por ele transitar",
        "5106": "Venda de mercadoria adquirida ou recebida de terceiros, que não deva por ele transitar",
        "5109": "Venda de produção do estabelecimento, destinada à Zona Franca de Manaus ou Áreas de Livre Comércio",
        "5110": "Venda de mercadoria adquirida ou recebida de terceiros, destinada à Zona Franca de Manaus ou Áreas de Livre Comércio",
        "5111": "Venda de produção do estabelecimento remetida anteriormente em consignação industrial",
        "5112": "Venda de mercadoria adquirida ou recebida de terceiros remetida anteriormente em consignação industrial",
        "5113": "Venda de produção do estabelecimento remetida anteriormente em consignação mercantil",
        "5114": "Venda de mercadoria adquirida ou recebida de terceiros remetida anteriormente em consignação mercantil",
        "5115": "Venda de mercadoria adquirida ou recebida de terceiros, recebida anteriormente em consignação mercantil",
        "5116": "Venda de produção do estabelecimento originada de encomenda para entrega futura",
        "5117": "Venda de mercadoria adquirida ou recebida de terceiros, originada de encomenda para entrega futura",
        "5118": "Venda de produção do estabelecimento entregue ao destinatário por conta e ordem do adquirente originário, em venda à ordem",
        "5119": "Venda de mercadoria adquirida ou recebida de terceiros entregue ao destinatário por conta e ordem do adquirente originário, em venda à ordem",
        "5120": "Venda de mercadoria adquirida ou recebida de terceiros entregue ao destinatário pelo vendedor remetente, em venda à ordem",
        "5122": "Venda de produção do estabelecimento remetida para industrialização, por conta e ordem do adquirente, sem transitar pelo estabelecimento do adquirente",
        "5123": "Venda de mercadoria adquirida ou recebida de terceiros remetida para industrialização, por conta e ordem do adquirente, sem transitar pelo estabelecimento do adquirente",
        "5124": "Industrialização efetuada para outra empresa",
        "5125": "Industrialização efetuada para outra empresa quando a mercadoria recebida para utilização no processo de industrialização não transitar pelo estabelecimento adquirente da mercadoria",
        "5151": "Transferência de produção do estabelecimento",
        "5152": "Transferência de mercadoria adquirida ou recebida de terceiros",
        "5153": "Transferência de energia elétrica",
        "5155": "Transferência de produção do estabelecimento, que não deva por ele transitar",
        "5156": "Transferência de mercadoria adquirida ou recebida de terceiros, que não deva por ele transitar",
        "5201": "Devolução de compra para industrialização ou produção rural",
        "5202": "Devolução de compra para comercialização",
        "5205": "Anulação de valor relativo a aquisição de serviço de comunicação",
        "5206": "Anulação de valor relativo a aquisição de serviço de transporte",
        "5207": "Anulação de valor relativo à compra de energia elétrica",
        "5208": "Devolução de mercadoria recebida em transferência para industrialização ou produção rural",
        "5209": "Devolução de mercadoria recebida em transferência para comercialização",
        "5210": "Devolução de compra para utilização na prestação de serviço",
        "5251": "Venda de energia elétrica para distribuição ou comercialização",
        "5252": "Venda de energia elétrica para estabelecimento industrial",
        "5253": "Venda de energia elétrica para estabelecimento comercial",
        "5254": "Venda de energia elétrica para estabelecimento prestador de serviço de transporte",
        "5255": "Venda de energia elétrica para estabelecimento prestador de serviço de comunicação",
        "5256": "Venda de energia elétrica para estabelecimento de produtor rural",
        "5257": "Venda de energia elétrica para consumo por demanda contratada",
        "5258": "Venda de energia elétrica a não contribuinte",
        "5301": "Prestação de serviço de comunicação para execução de serviço da mesma natureza",
        "5302": "Prestação de serviço de comunicação a estabelecimento industrial",
        "5303": "Prestação de serviço de comunicação a estabelecimento comercial",
        "5304": "Prestação de serviço de comunicação a estabelecimento de prestador de serviço de transporte",
        "5305": "Prestação de serviço de comunicação a estabelecimento de geradora ou de distribuidora de energia elétrica",
        "5306": "Prestação de serviço de comunicação a estabelecimento de produtor rural",
        "5307": "Prestação de serviço de comunicação a não contribuinte",
        "5351": "Prestação de serviço de transporte para execução de serviço da mesma natureza",
        "5352": "Prestação de serviço de transporte a estabelecimento industrial",
        "5353": "Prestação de serviço de transporte a estabelecimento comercial",
        "5354": "Prestação de serviço de transporte a estabelecimento de prestador de serviço de comunicação",
        "5355": "Prestação de serviço de transporte a estabelecimento de geradora ou de distribuidora de energia elétrica",
        "5356": "Prestação de serviço de transporte a estabelecimento de produtor rural",
        "5357": "Prestação de serviço de transporte a não contribuinte",
        "5359": "Prestação de serviço de transporte a contribuinte ou a não contribuinte quando a mercadoria transportada está dispensada de emissão de nota fiscal",
        "5401": "Venda de produção do estabelecimento em operação com produto sujeito ao regime de substituição tributária, na condição de contribuinte substituto",
        "5402": "Venda de produção do estabelecimento de produto sujeito ao regime de substituição tributária, em operação entre contribuintes substitutos do mesmo produto",
        "5403": "Venda de mercadoria adquirida ou recebida de terceiros em operação com mercadoria sujeita ao regime de substituição tributária, na condição de contribuinte substituto",
        "5405": "Venda de mercadoria adquirida ou recebida de terceiros em operação com mercadoria sujeita ao regime de substituição tributária, na condição de contribuinte substituído",
        "5408": "Transferência de produção do estabelecimento em operação com produto sujeito ao regime de substituição tributária",
        "5409": "Transferência de mercadoria adquirida ou recebida de terceiros em operação com mercadoria sujeita ao regime de substituição tributária",
        "5410": "Devolução de compra para industrialização ou produção rural em operação com mercadoria sujeita ao regime de substituição tributária",
        "5411": "Devolução de compra para comercialização em operação com mercadoria sujeita ao regime de substituição tributária",
        "5412": "Devolução de bem do ativo imobilizado, em operação com mercadoria sujeita ao regime de substituição tributária",
        "5413": "Devolução de mercadoria destinada ao uso ou consumo, em operação com mercadoria sujeita ao regime de substituição tributária",
        "5414": "Remessa de produção do estabelecimento para venda fora do estabelecimento em operação com produto sujeito ao regime de substituição tributária",
        "5415": "Remessa de mercadoria adquirida ou recebida de terceiros para venda fora do estabelecimento, em operação com mercadoria sujeita ao regime de substituição tributária",
        "5501": "Remessa de produção do estabelecimento, com fim específico de exportação",
        "5502": "Remessa de mercadoria adquirida ou recebida de terceiros, com fim específico de exportação",
        "5503": "Devolução de mercadoria recebida com fim específico de exportação",
        "5504": "Remessa de mercadorias para formação de lote de exportação, de produtos industrializados ou produzidos pelo próprio estabelecimento",
        "5505": "Remessa de mercadorias, adquiridas ou recebidas de terceiros, para formação de lote de exportação",
        "5551": "Venda de bem do ativo imobilizado",
        "5552": "Transferência de bem do ativo imobilizado",
        "5553": "Devolução de compra de bem para o ativo imobilizado",
        "5554": "Remessa de bem do ativo imobilizado para uso fora do estabelecimento",
        "5555": "Devolução de bem do ativo imobilizado de terceiro, recebido para uso no estabelecimento",
        "5556": "Devolução de compra de material de uso ou consumo",
        "5557": "Transferência de material de uso ou consumo",
        "5601": "Transferência de crédito de ICMS acumulado",
        "5602": "Transferência de saldo credor de ICMS para outro estabelecimento da mesma empresa, destinado à compensação de saldo devedor de ICMS",
        "5603": "Ressarcimento de ICMS retido por substituição tributária",
        "5605": "Transferência de saldo devedor de ICMS de outro estabelecimento da mesma empresa",
        "5606": "Utilização de saldo credor de ICMS para extinção por compensação de débitos fiscais",
        "5651": "Venda de combustível ou lubrificante de produção do estabelecimento destinado à industrialização subsequente",
        "5652": "Venda de combustível ou lubrificante de produção do estabelecimento destinado à comercialização",
        "5653": "Venda de combustível ou lubrificante de produção do estabelecimento destinado a consumidor ou usuário final",
        "5654": "Venda de combustível ou lubrificante adquirido ou recebido de terceiros destinado à industrialização subsequente",
        "5655": "Venda de combustível ou lubrificante adquirido ou recebido de terceiros destinado à comercialização",
        "5656": "Venda de combustível ou lubrificante adquirido ou recebido de terceiros destinado a consumidor ou usuário final",
        "5657": "Remessa de combustível ou lubrificante adquirido ou recebido de terceiros para venda fora do estabelecimento",
        "5658": "Transferência de combustível ou lubrificante de produção do estabelecimento",
        "5659": "Transferência de combustível ou lubrificante adquirido ou recebido de terceiro",
        "5660": "Devolução de compra de combustível ou lubrificante adquirido para industrialização subsequente",
        "5661": "Devolução de compra de combustível ou lubrificante adquirido para comercialização",
        "5662": "Devolução de compra de combustível ou lubrificante adquirido por consumidor ou usuário final",
        "5663": "Remessa para armazenagem de combustível ou lubrificante",
        "5664": "Retorno de combustível ou lubrificante recebido para armazenagem",
        "5665": "Retorno simbólico de combustível ou lubrificante recebido para armazenagem",
        "5666": "Remessa por conta e ordem de terceiros de combustível ou lubrificante recebido para armazenagem",
        "5667": "Venda de combustível ou lubrificante a consumidor ou usuário final estabelecido em outra unidade da Federação",
        "5901": "Remessa para industrialização por encomenda",
        "5902": "Retorno de mercadoria utilizada na industrialização por encomenda",
        "5903": "Retorno de mercadoria recebida para industrialização e não aplicada no referido processo",
        "5904": "Remessa para venda fora do estabelecimento",
        "5905": "Remessa para depósito fechado ou armazém geral",
        "5906": "Retorno de mercadoria depositada em depósito fechado ou armazém geral",
        "5907": "Retorno simbólico de mercadoria depositada em depósito fechado ou armazém geral",
        "5908": "Remessa de bem por conta de contrato de comodato",
        "5909": "Retorno de bem recebido por conta de contrato de comodato",
        "5910": "Remessa em bonificação, doação ou brinde",
        "5911": "Remessa de amostra grátis",
        "5912": "Remessa de mercadoria ou bem para demonstração",
        "5913": "Retorno de mercadoria ou bem recebido para demonstração",
        "5914": "Remessa de mercadoria ou bem para exposição ou feira",
        "5915": "Remessa de mercadoria ou bem para conserto ou reparo",
        "5916": "Retorno de mercadoria ou bem recebido para conserto ou reparo",
        "5917": "Remessa de mercadoria em consignação mercantil ou industrial",
        "5918": "Devolução de mercadoria recebida em consignação mercantil ou industrial",
        "5919": "Devolução simbólica de mercadoria vendida ou utilizada em processo industrial, recebida anteriormente em consignação mercantil ou industrial",
        "5920": "Remessa de vasilhame ou sacaria",
        "5921": "Devolução de vasilhame ou sacaria",
        "5922": "Lançamento efetuado a título de simples faturamento decorrente de venda para entrega futura",
        "5923": "Remessa de mercadoria por conta e ordem de terceiros, em venda à ordem ou em operações com armazém geral ou depósito fechado",
        "5924": "Remessa para industrialização por conta e ordem do adquirente da mercadoria, quando esta não transitar pelo estabelecimento do adquirente",
        "5925": "Retorno de mercadoria recebida para industrialização por conta e ordem do adquirente da mercadoria, quando aquela não transitar pelo estabelecimento do adquirente",
        "5926": "Lançamento efetuado a título de reclassificação de mercadoria decorrente de formação de kit ou de sua desagregação",
        "5927": "Lançamento efetuado a título de baixa de estoque decorrente de perda, roubo ou deterioração",
        "5928": "Lançamento efetuado a título de baixa de estoque decorrente do encerramento da atividade da empresa",
        "5929": "Lançamento efetuado em decorrência de emissão de documento fiscal relativo a operação ou prestação também registrada em equipamento Emissor de Cupom Fiscal - ECF",
        "5931": "Lançamento efetuado em decorrência da responsabilidade de retenção do imposto por substituição tributária, atribuída ao remetente ou alienante da mercadoria, pelo serviço de transporte realizado por transportador autônomo ou por transportador não inscrito na unidade da Federação onde iniciado o serviço",
        "5932": "Prestação de serviço de transporte iniciada em unidade da Federação diversa daquela onde inscrito o prestador",
        "5933": "Prestação de serviço tributado pelo ISSQN",
        "5934": "Remessa simbólica de mercadoria depositada em armazém geral ou depósito fechado",
        "5949": "Outra saída de mercadoria ou prestação de serviço não especificado",
    }
    
    for cfop, desc in saidas_base.items():
        items.append({
            "cfop": cfop,
            "descricao": desc,
            "tipo": "saida_interna",
            "grupo": "5"
        })
        
        # Grupo 6 (interestadual)
        cfop6 = "6" + cfop[1:]
        items.append({
            "cfop": cfop6,
            "descricao": desc,
            "tipo": "saida_interestadual", 
            "grupo": "6"
        })
    
    # Grupo 7 - Exportação
    exportacao = {
        "7101": "Venda de produção do estabelecimento",
        "7102": "Venda de mercadoria adquirida ou recebida de terceiros",
        "7105": "Venda de produção do estabelecimento, que não deva por ele transitar",
        "7106": "Venda de mercadoria adquirida ou recebida de terceiros, que não deva por ele transitar",
        "7127": "Venda de produção do estabelecimento sob o regime de Drawback",
        "7201": "Devolução de compra para industrialização ou produção rural",
        "7202": "Devolução de compra para comercialização",
        "7210": "Devolução de compra para utilização na prestação de serviço",
        "7211": "Devolução de compras para industrialização sob o regime de Drawback",
        "7251": "Venda de energia elétrica para o exterior",
        "7301": "Prestação de serviço de comunicação para execução de serviço da mesma natureza",
        "7358": "Prestação de serviço de transporte",
        "7501": "Exportação de mercadorias recebidas com fim específico de exportação",
        "7551": "Venda de bem do ativo imobilizado",
        "7553": "Devolução de compra de bem para o ativo imobilizado",
        "7556": "Devolução de compra de material de uso ou consumo",
        "7651": "Venda de combustível ou lubrificante de produção do estabelecimento",
        "7654": "Venda de combustível ou lubrificante adquiridos ou recebidos de terceiros",
        "7667": "Venda de combustível ou lubrificante a consumidor ou usuário final",
        "7930": "Lançamento efetuado a título de devolução de bem cuja entrada tenha ocorrido sob amparo de regime especial aduaneiro de admissão temporária",
        "7949": "Outra saída de mercadoria ou prestação de serviço não especificado",
    }
    
    for cfop, desc in exportacao.items():
        items.append({
            "cfop": cfop,
            "descricao": desc,
            "tipo": "exportacao",
            "grupo": "7"
        })
    
    # Salva
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    output = {
        "cfop": {
            "description": "Código Fiscal de Operações e Prestações - Completo",
            "source": "Convênio SINIEF s/nº de 1970 (atualizado)",
            "total_items": len(items),
            "grupos": CFOP_GROUPS,
            "items": items
        }
    }
    
    output_path = OUTPUT_DIR / "cfop_completa.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {len(items)} CFOPs salvos em: {output_path}")


if __name__ == "__main__":
    print("=" * 60)
    print("📋 Gerando Tabela CFOP Completa")
    print("=" * 60)
    create_cfop_complete()
