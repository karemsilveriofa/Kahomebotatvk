import time
import requests
import telegram
from datetime import datetime
from flask import Flask
import threading

# === CONFIGURAÇÕES ===
API_KEY = "c95f42c34f934f91938f91e5cc8604a6"
TELEGRAM_TOKEN = "7239698274:AAFyg7HWLPvXceJYDope17DkfJpxtU4IU2Y"
TELEGRAM_ID = "6821521589"
INTERVALO = "1min"

# === Inicializa o bot Telegram ===
bot = telegram.Bot(token=TELEGRAM_TOKEN)

# === Flask para manter serviço ativo na Render ===
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot de sinais ativo!"

# === Ler ativo do arquivo ativo.txt ===
def obter_ativo():
    try:
        with open("ativo.txt", "r") as f:
            return f.read().strip()
    except:
        return "AUDCHF"  # padrão

# === Enviar mensagem Telegram ===
def enviar_sinal(texto):
    try:
        bot.send_message(chat_id=TELEGRAM_ID, text=texto)
        print(f"[{datetime.now()}] Sinal enviado: {texto}")
    except Exception as e:
        print(f"[ERRO] Não foi possível enviar sinal: {e}")

# === Obter dados da API Twelve Data ===
def obter_candles(ativo, intervalo):
    url = (
        f"https://api.twelvedata.com/time_series?"
        f"symbol={ativo}&interval={intervalo}&apikey={API_KEY}&outputsize=3"
    )
    try:
        resposta = requests.get(url)
        dados = resposta.json()
        if "values" in dados:
            return dados["values"]
        else:
            print(f"[ERRO API] {dados}")
            return None
    except Exception as e:
        print(f"[ERRO] Falha na requisição API: {e}")
        return None

# === Função principal que calcula a direção da próxima vela ===
def calcular_sinal():
    ativo = obter_ativo()
    candles = obter_candles(ativo, INTERVALO)
    if not candles or len(candles) < 2:
        print("[AVISO] Dados insuficientes para cálculo")
        return

    # A API retorna candles do mais recente para o mais antigo:
    # candles[0] = vela mais recente (última fechada)
    # candles[1] = vela anterior
    vela_mais_recente = candles[0]
    vela_anterior = candles[1]

    fechamento_recente = float(vela_mais_recente["close"])
    fechamento_anterior = float(vela_anterior["close"])

    # Se preço subiu, próxima vela deve subir (sinal compra), senão venda
    if fechamento_recente > fechamento_anterior:
        direcao = "📈 COMPRA"
    elif fechamento_recente < fechamento_anterior:
        direcao = "📉 VENDA"
    else:
        direcao = "⏸️ SEM MOVIMENTO"

    horario = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    mensagem = (
        f"SINAL DE TRADING\n"
        f"Ativo: {ativo}\n"
        f"Direção prevista: {direcao}\n"
        f"Preço último fechamento: R${fechamento_recente:.5f}\n"
        f"Horário do sinal: {horario}"
    )

    enviar_sinal(mensagem)

# === Loop que executa a verificação a cada 60 segundos ===
def iniciar_bot():
    enviar_sinal("✅ Bot de sinais iniciado com sucesso!")
    while True:
        calcular_sinal()
        time.sleep(60)

# === Thread para rodar o bot paralelamente ao Flask ===
threading.Thread(target=iniciar_bot).start()

# === Executar Flask para manter o serviço ativo ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
    
