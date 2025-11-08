import os, yaml
from dotenv import load_dotenv


load_dotenv()


APP_PORT = int(os.getenv("APP_PORT", "5000"))
DB_URL = os.getenv("DB_URL", "sqlite:///./reef.db")
SENSOR_DRIVER = os.getenv("SENSOR_DRIVER", "sensors_sim")
GPIO_DRIVER = os.getenv("GPIO_DRIVER", "gpio")


with open("config.yaml", "r") as f:
CONFIG = yaml.safe_load(f)