import time
from datetime import datetime, timedelta
import pytz

# Variáveis globais
preco_anterior = None
ultimo_sinal_enviado = None
ultimo_envio_tempo = datetime.min  # controla intervalo entre sinais

# Intervalo máximo entre sinais (em segundos)
INTERVALO_MINIMO_SINAL = 120  # 2 minutos

def monitorar():
    global preco_anterior, ultimo_sinal_enviado, ultimo_envio_tempo
    fuso_brasilia = pytz.timezone("America/Sao_Paulo")

    while True:
        if not bot_ativo():
            print("⛔ Bot desligado")
            time.sleep(10)
            continue

        agora = datetime.now(fuso_brasilia)

        # Verifica se já passou o intervalo mínimo para enviar próximo sinal
        if (agora - ultimo_envio_tempo).total_seconds() < INTERVALO_MINIMO_SINAL:
            time.sleep(1)
            continue

        ativo = obter_ativo()
        preco, rsi, ma5, ma20 = obter_dados(ativo)

        if preco is None or rsi is None or ma5 is None or ma20 is None:
            print("Dados incompletos. Pulando ciclo.")
            time.sleep(5)
            continue

        entrada_em = agora + timedelta(seconds=10)
        chave_sinal = entrada_em.strftime("%Y-%m-%d %H:%M")
        horario_entrada = entrada_em.strftime("%H:%M:%S")

        if ultimo_sinal_enviado == chave_sinal:
            time.sleep(1)
            continue

        mensagem = f"📊 {ativo} - ${preco:.5f}\n"

        if preco_anterior:
            variacao = ((preco - preco_anterior) / preco_anterior) * 100
            mensagem += f"🔄 Variação: {variacao:.4f}%\n"
        else:
            variacao = 0
            mensagem += "🟡 Iniciando monitoramento...\n"

        preco_anterior = preco
        sinal = "⚪ SEM AÇÃO"

        # Estratégia melhorada:
        # RSI < 35 = sobrevenda = COMPRA
        # RSI > 65 = sobrecompra = VENDA
        # Cruzamento das médias móveis confirmam a tendência
        # Variação mínima para sensibilidade (0.005%)
        if (rsi < 35 and ma5 > ma20 and variacao > 0.005):
            sinal = f"🟢 COMPRA às {horario_entrada}"
        elif (rsi > 65 and ma5 < ma20 and variacao < -0.005):
            sinal = f"🔴 VENDA às {horario_entrada}"

        if "COMPRA" in sinal or "VENDA" in sinal:
            mensagem += f"📈 RSI: {rsi:.2f}\n"
            mensagem += f"📉 MA5: {ma5:.5f} | MA20: {ma20:.5f}\n"
            mensagem += f"📍 SINAL: {sinal}"
            enviar_sinal(mensagem)
            ultimo_sinal_enviado = chave_sinal
            ultimo_envio_tempo = agora
        else:
            print(f"{agora.strftime('%H:%M:%S')} - Sem sinal relevante.")

        time.sleep(1)
        
