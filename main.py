import time
import requests
from telegram import Bot
from datetime import datetime
from flask import Flask
import threading
import pytz

# === CONFIGURAÇÕES ===
API_KEY = "c95f42c34f934f91938f91e5cc8604a6"
TOKEN = '7239698274:AAFyg7HWLPvXceJYDope17DkfJpxtU4IU2Y'
CHAT_ID = 6821521589
INTERVALO = "1min"

bot = Bot(token=TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot de sinais ativo com precisão aprimorada!"

# === Obter o ativo do arquivo ===
def obter_ativo():
    try:
        with open("ativo.txt", "r") as f:
            ativo = f.read().strip()
            print(f"[INFO] Ativo lido: {ativo}")
            return ativo
    except Exception as e:
        print(f"[ERRO] Falha ao ler ativo.txt: {e}")
        return "CAD/CHF"  # valor padrão

# === Enviar mensagem pelo Telegram ===
def enviar_sinal(texto):
    try:
        bot.send_message(chat_id=CHAT_ID, text=texto)
        print(f"[ENVIADO] {texto}")
    except Exception as e:
        print(f"[ERRO TELEGRAM] {e}")

# === Obter candles da API ===
def obter_candles(ativo):
    url = f"https://api.twelvedata.com/time_series?symbol={ativo}&interval={INTERVALO}&apikey={API_KEY}&outputsize=3"
    try:
        resposta = requests.get(url)
        dados = resposta.json()
        print(f"[API] Resposta: {dados}")  # DEBUG

        if "values" in dados:
            return dados["values"]
        else:
            erro = dados.get("message", "Erro desconhecido")
            enviar_sinal(f"❌ Erro na API para {ativo}: {erro}")
            return None
    except Exception as e:
        print(f"[ERRO API] {e}")
        return None

# === Análise mais precisa ===
def candle_info(candle):
    open_price = float(candle["open"])
    close_price = float(candle["close"])
    high = float(candle["high"])
    low = float(candle["low"])
    corpo = abs(close_price - open_price)
    pavio = (high - low) - corpo
    return open_price, close_price, corpo, pavio

# === Lógica de cálculo e envio do sinal ===
def calcular_sinal():
    ativo = obter_ativo()
    candles = obter_candles(ativo)

    if not candles or len(candles) < 2:
        msg = f"[AVISO] Dados insuficientes para {ativo}. Nenhum sinal gerado."
        print(msg)
        enviar_sinal(msg)
        return

    atual = candles[0]
    anterior = candles[1]

    o1, c1, corpo1, pavio1 = candle_info(anterior)
    o2, c2, corpo2, pavio2 = candle_info(atual)

    print(f"[DADOS] Último candle: {c2:.5f}, Anterior: {c1:.5f}")
    print(f"[DETALHES] Corpo1: {corpo1:.5f}, Pavio1: {pavio1:.5f}")

    # Regras mais sensíveis
    if corpo1 < pavio1 * 0.5:
        direcao = "⏸️ LATERAL (vela de indecisão)"
    elif c2 > c1:
        direcao = "📈 COMPRA"
    elif c2 < c1:
        direcao = "📉 VENDA"
    else:
        direcao = "⏸️ SEM DIREÇÃO"

    horario_brasilia = datetime.now(pytz.timezone("America/Sao_Paulo")).strftime('%H:%M:%S')

    mensagem = (
        f"🔔 SINAL DE ENTRADA\n"
        f"Ativo: {ativo}\n"
        f"Direção: {direcao}\n"
        f"Fechamento anterior: {c1:.5f}\n"
        f"Fechamento atual: {c2:.5f}\n"
        f"Horário (Brasília): {horario_brasilia}"
    )

    enviar_sinal(mensagem)

# === Loop principal do bot ===
def iniciar_bot():
    enviar_sinal("✅ Bot de sinais iniciado com precisão aprimorada!")
    while True:
        print("[LOOP] Executando nova análise...")
        calcular_sinal()
        time.sleep(60)

# === Início em thread separada ===
threading.Thread(target=iniciar_bot).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
    
