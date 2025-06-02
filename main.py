import time
import requests
import telegram
from datetime import datetime
from flask import Flask
import threading
import pytz  # ✅ Importa o módulo para fusos horários

# === CONFIGURAÇÕES ===
API_KEY = "c95f42c34f934f91938f91e5cc8604a6"
TELEGRAM_TOKEN = "7239698274:AAFyg7HWLPvXceJYDope17DkfJpxtU4IU2Y"
TELEGRAM_ID = "6821521589"
INTERVALO = "1min"

bot = telegram.Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot de sinais ativo!"

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
        bot.send_message(chat_id=TELEGRAM_ID, text=texto)
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

# === Lógica de cálculo e envio do sinal ===
def calcular_sinal():
    ativo = obter_ativo()
    candles = obter_candles(ativo)

    if not candles or len(candles) < 2:
        msg = f"[AVISO] Dados insuficientes para {ativo}. Nenhum sinal gerado."
        print(msg)
        enviar_sinal(msg)
        return

    ultima = candles[0]
    anterior = candles[1]

    fechamento_atual = float(ultima["close"])
    fechamento_passado = float(anterior["close"])

    print(f"[DADOS] Último: {fechamento_atual}, Anterior: {fechamento_passado}")

    if fechamento_atual > fechamento_passado:
        direcao = "📈 COMPRA"
    elif fechamento_atual < fechamento_passado:
        direcao = "📉 VENDA"
    else:
        direcao = "⏸️ LATERAL"

    # ✅ Hora no fuso de Brasília
    horario_brasilia = datetime.now(pytz.timezone("America/Sao_Paulo")).strftime('%H:%M:%S')

    mensagem = (
        f"SINAL DE ENTRADA 🔔\n"
        f"Ativo: {ativo}\n"
        f"Direção: {direcao}\n"
        f"Fechamento anterior: {fechamento_passado:.5f}\n"
        f"Fechamento atual: {fechamento_atual:.5f}\n"
        f"Horário: {horario_brasilia}"
    )

    enviar_sinal(mensagem)

# === Loop que roda a análise a cada minuto ===
def iniciar_bot():
    enviar_sinal("✅ Bot de sinais iniciado com sucesso!")
    while True:
        print("[LOOP] Executando nova análise...")
        calcular_sinal()
        time.sleep(60)

# === Thread principal ===
threading.Thread(target=iniciar_bot).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
    
