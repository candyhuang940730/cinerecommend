import ngrok
from dotenv import load_dotenv

load_dotenv()  # 必須在 ngrok.forward 之前

def connect_ngrok():
    forwarder = ngrok.forward(
        "localhost:5432",
        authtoken_from_env=True,
        domain="granite-ranger-prone.ngrok-free.dev",
    )
    print(f"Available at: {forwarder.url()}")

connect_ngrok()