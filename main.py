import time
import requests
import telegram
from datetime import datetime, timedelta
import pytz
import threading
from flask import Flask
import os

# === CONFIGURAÇÕES via Variáveis de Ambiente ===
API_KEY = os.getenv("API_KEY")
INTERVAL = "1min"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_ID = os.getenv("TELEGRAM_ID")
PORT = int(os.getenv("PORT", 10000))
bot = telegram.Bot(token=TELEGRAM_TOKEN)

preco_anterior = None
ultimo_sinal_enviado = None

def obter_ativo():
    try:
        with open("ativo.txt", "r") as f:
            ativo = f.read().strip().upper()
            if "(OTC" in ativo:
                ativo = ativo.split("(")[0].strip()
            return ativo
    except:
        return "EUR/USD"

def bot_ativo():
    try:
        with open("status.txt", "r") as f:
            return f.read().strip().upper() == "ON"
    except:
        return True

def obter_dados(symbol):
    try:
        preco_url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={INTERVAL}&apikey={API_KEY}&outputsize=2"
        preco_data = requests.get(preco_url).json()
        if "values" not in preco_data:
            raise Exception(preco_data.get("message", "Erro desconhecido"))
        preco = float(preco_data["values"][0]["close"])

        rsi_url = f"https://api.twelvedata.com/rsi?symbol={symbol}&interval={INTERVAL}&apikey={API_KEY}&time_period=14"
        rsi_data = requests.get(rsi_url).json()
        rsi = float(rsi_data["values"][0]["rsi"]) if "values" in rsi_data else None

        ma5_url = f"https://api.twelvedata.com/ma?symbol={symbol}&interval={INTERVAL}&apikey={API_KEY}&time_period=5&type=sma"
        ma20_url = f"https://api.twelvedata.com/ma?symbol={symbol}&interval={INTERVAL}&apikey={API_KEY}&time_period=20&type=sma"
        ma5_data = requests.get(ma5_url).json()
        ma20_data = requests.get(ma20_url).json()
        ma5 = float(ma5_data["values"][0]["ma"]) if "values" in ma5_data else None
        ma20 = float(ma20_data["values"][0]["ma"]) if "values" in ma20_data else None

        return preco, rsi, ma5, ma20
    except Exception as e:
        print("Erro ao obter dados:", e)
        return None, None, None, None

def enviar_sinal(mensagem):
    try:
        bot.send_message(chat_id=TELEGRAM_ID, text=mensagem)
        print(f"Sinal enviado: {mensagem}")
    except Exception as e:
        print("Erro ao enviar:", e)

def monitorar():
    global preco_anterior, ultimo_sinal_enviado
    fuso_brasilia = pytz.timezone("America/Sao_Paulo")

    while True:
        if not bot_ativo():
            print("⛔ Bot desligado")
            time.sleep(10)
            continue

        agora = datetime.now(fuso_brasilia)
        segundos = agora.second

        if segundos != 50:
            time.sleep(1)
            continue

        ativo = obter_ativo()
        preco, rsi, ma5, ma20 = obter_dados(ativo)
        agora = datetime.now(fuso_brasilia)
        entrada_em = agora + timedelta(seconds=10)

        chave_sinal = entrada_em.strftime("%Y-%m-%d %H:%M")
        horario_entrada = entrada_em.strftime("%H:%M:%S")

        if preco and rsi and ma5 and ma20:
            if ultimo_sinal_enviado == chave_sinal:
                continue

            mensagem = f"📊 {ativo} - ${preco:.5f}\n"

            if preco_anterior:
                variacao = ((preco - preco_anterior) / preco_anterior) * 100
                mensagem += f"🔄 Variação: {variacao:.3f}%\n"
            else:
                variacao = 0
                mensagem += "🟡 Iniciando monitoramento...\n"

            preco_anterior = preco
            sinal = "⚪ SEM AÇÃO"

            if rsi < 45 or (ma5 > ma20 and variacao > 0.01):
                sinal = f"🟢 COMPRA às {horario_entrada}"
            elif rsi > 55 or (ma5 < ma20 and variacao < -0.01):
                sinal = f"🔴 VENDA às {horario_entrada}"

            if "COMPRA" in sinal or "VENDA" in sinal:
                mensagem += f"📈 RSI: {rsi:.2f}\n"
                mensagem += f"📉 MA5: {ma5:.5f} | MA20: {ma20:.5f}\n"
                mensagem += f"📍 SINAL: {sinal}"
                enviar_sinal(mensagem)
                ultimo_sinal_enviado = chave_sinal

        time.sleep(1)

# Iniciar thread do monitoramento
threading.Thread(target=monitorar, daemon=True).start()

# Flask App para manter o serviço vivo na Render
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Bot de sinais está online."

@app.route("/ping")
def ping():
    return "pong"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
    
