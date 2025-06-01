import time
import requests
import telegram
from datetime import datetime, timedelta
import pytz
import threading
from flask import Flask

# === CONFIGURAÇÕES ===
API_KEY = "c95f42c34f934f91938f91e5cc8604a6"
SYMBOL = "EUR/USD"
INTERVAL = "1min"

TELEGRAM_TOKEN = "7239698274:AAFyg7HWLPvXceJYDope17DkfJpxtU4IU2Y"
TELEGRAM_ID = "6821521589"

FUSO = pytz.timezone('America/Sao_Paulo')
app = Flask(__name__)

# Inicializa o bot
try:
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    bot.get_me()  # valida token
except telegram.error.InvalidToken:
    print("❌ ERRO: Token do Telegram inválido. Verifique.")
    exit()

ultimo_sinal_enviado = ""
ultimo_envio = datetime.now(FUSO) - timedelta(minutes=5)

def obter_dados():
    url = f"https://api.twelvedata.com/time_series?symbol={SYMBOL}&interval={INTERVAL}&apikey={API_KEY}&outputsize=20&indicators=ma,ma:5,ma:20,rsi"
    resposta = requests.get(url)
    try:
        dados = resposta.json()
        valores = dados['values']
        rsi = float(valores[0]['rsi'])
        ma5 = float(valores[0]['ma5'])
        ma20 = float(valores[0]['ma20'])
        close_atual = float(valores[0]['close'])
        close_anterior = float(valores[1]['close'])
        variacao = (close_atual - close_anterior) / close_anterior
        return rsi, ma5, ma20, variacao, close_atual
    except:
        print("❌ Erro ao obter dados")
        return None

def enviar_sinal(mensagem):
    try:
        bot.send_message(chat_id=TELEGRAM_ID, text=mensagem)
    except telegram.error.TelegramError as e:
        print(f"❌ Erro ao enviar mensagem no Telegram: {e}")

def monitorar():
    global ultimo_sinal_enviado, ultimo_envio
    while True:
        agora = datetime.now(FUSO)
        if (agora - ultimo_envio).total_seconds() < 180:
            time.sleep(10)
            continue

        print(f"\n⏱️ Verificando às {agora.strftime('%H:%M:%S')}")
        dados = obter_dados()
        if not dados:
            time.sleep(60)
            continue

        rsi, ma5, ma20, variacao, preco = dados
        horario_entrada = agora.strftime("%H:%M:%S")
        chave_sinal = f"{rsi:.2f}-{ma5:.5f}-{ma20:.5f}"

        sinal = None

        # === FILTROS DE PRECISÃO AJUSTADOS (mais sensíveis) ===
        if rsi < 52 and ma5 > ma20 and variacao > 0.001:
            sinal = f"🟢 COMPRA às {horario_entrada}"
        elif rsi > 48 and ma5 < ma20 and variacao < -0.001:
            sinal = f"🔴 VENDA às {horario_entrada}"

        if sinal and chave_sinal != ultimo_sinal_enviado:
            mensagem = (
                f"📊 RSI: {rsi:.2f}\n"
                f"📈 MA5: {ma5:.5f} | MA20: {ma20:.5f}\n"
                f"📉 Variação: {variacao:.3%}\n"
                f"🚨 SINAL: {sinal}"
            )
            enviar_sinal(mensagem)
            ultimo_sinal_enviado = chave_sinal
            ultimo_envio = agora
            print("✅ Sinal enviado:", sinal)
        else:
            print("⚠️ Nenhum sinal novo ou critérios não atendidos.")

        time.sleep(60)

@app.route('/ping')
def ping():
    return "Bot está online 🟢"

if __name__ == "__main__":
    threading.Thread(target=monitorar).start()
    app.run(host="0.0.0.0", port=10000)
    
