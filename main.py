import time
import requests
import telegram
from datetime import datetime, timedelta
import pytz
import threading
from flask import Flask

# === CONFIGURAÇÕES ===
API_KEY = "c95f42c34f934f91938f91e5cc8604a6"
TELEGRAM_TOKEN = "7239698274:AAFyg7HWLPvXceJYDope17DkfJpxtU4IU2Y"
TELEGRAM_ID = "6821521589"
INTERVALO = "1min"
VARIACAO_MINIMA = 0.0005  # 0.05%

# === BOT TELEGRAM ===
bot = telegram.Bot(token=TELEGRAM_TOKEN)

# === FLASK PARA MANTER RENDER ATIVO ===
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot de Sinais Ativo!"

# === ENVIAR SINAL ===
def enviar_sinal(mensagem):
    try:
        bot.send_message(chat_id=TELEGRAM_ID, text=mensagem)
        print(f"[{datetime.now()}] SINAL ENVIADO: {mensagem}")
    except Exception as e:
        print(f"[ERRO] Falha ao enviar mensagem: {e}")

# === OBTER ATIVO ===
def obter_ativo():
    try:
        with open("ativo.txt", "r") as f:
            return f.read().strip()
    except:
        return "PETR4.SA"  # padrão se não encontrar o arquivo

# === VERIFICAR SINAL ===
def verificar_sinal():
    ativo = obter_ativo()
    print(f"[INFO] Verificando ativo: {ativo}")
    url = f"https://api.twelvedata.com/time_series?symbol={ativo}&interval={INTERVALO}&apikey={API_KEY}&outputsize=2"
    try:
        response = requests.get(url)
        data = response.json()

        candles = data.get("values", [])
        if len(candles) < 2:
            print("[AVISO] Não há candles suficientes")
            return

        atual = float(candles[0]["close"])
        anterior = float(candles[1]["close"])

        variacao = abs(atual - anterior) / anterior
        print(f"[INFO] Variação: {variacao*100:.4f}%")

        if variacao >= VARIACAO_MINIMA:
            direcao = "📈 COMPRA" if atual > anterior else "📉 VENDA"
            mensagem = f"SINAL GERADO\nAtivo: {ativo}\n{direcao}\nPreço: R${atual:.2f}\nHorário: {datetime.now().strftime('%H:%M:%S')}"
            enviar_sinal(mensagem)

    except Exception as e:
        print(f"[ERRO] Falha ao verificar sinal: {e}")

# === LOOP PRINCIPAL ===
def iniciar_bot():
    print("[INFO] Bot iniciado. Enviando mensagem de teste...")
    enviar_sinal("✅ Bot de sinais iniciado com sucesso!")

    while True:
        verificar_sinal()
        time.sleep(120)  # Aguarda 2 minutos entre verificações

# === THREAD DO BOT ===
threading.Thread(target=iniciar_bot).start()

# === EXECUTA FLASK ===
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
    
