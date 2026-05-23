# 🤖 APEX Bot — Paper Trading 24/7

Bot de paper trading con dashboard web. Opera automáticamente con precios reales de Kraken.

---

## 📁 Estructura del proyecto

```
apex_bot/
├── bot2/
│   ├── __init__.py
│   ├── feed.py        ← Precios reales de Kraken
│   ├── indicators.py  ← EMA, RSI, MACD
│   ├── strategy.py    ← Señales de entrada
│   ├── portfolio.py   ← Capital, trades, PnL
│   └── main.py        ← Servidor Flask + SocketIO
├── templates2/
│   └── index.html     ← Dashboard web
├── wsgi.py            ← Punto de entrada para Render
├── requirements.txt
├── Procfile
└── README.md
```

---

## 🚀 Guía de deploy paso a paso

### PASO 1 — Crear cuenta en GitHub

1. Ir a [github.com](https://github.com) → **Sign up**
2. Elegir username, email, contraseña
3. Verificar email
4. Plan gratuito es suficiente ✅

---

### PASO 2 — Subir el proyecto a GitHub

1. Logueado en GitHub, click en **"+"** (arriba a la derecha) → **New repository**
2. Nombre: `apex-bot`
3. Visibilidad: **Private** (recomendado)
4. Click **Create repository**
5. En la página del repositorio vacío, click en **"uploading an existing file"**
6. Subir **todos** los archivos manteniendo la estructura de carpetas:
   - Arrastrar la carpeta `apex_bot` completa
   - O subir archivo por archivo respetando las rutas
7. Click **Commit changes** → listo ✅

> ⚠️ Asegurate de que la estructura sea exactamente así en GitHub:
> ```
> apex-bot/
> ├── bot2/
> ├── templates2/
> ├── wsgi.py
> ├── requirements.txt
> └── Procfile
> ```

---

### PASO 3 — Conectar GitHub con Render

1. Ir a [render.com](https://render.com) → loguearse
2. Dashboard → **New +** → **Web Service**
3. Click **Connect GitHub** → autorizar Render
4. Seleccionar el repositorio `apex-bot`
5. Click **Connect**

---

### PASO 4 — Configurar el servicio en Render

Completar el formulario así:

| Campo | Valor |
|-------|-------|
| **Name** | apex-bot |
| **Region** | Oregon (US West) — más barato |
| **Branch** | main |
| **Root Directory** | *(dejar vacío)* |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn wsgi:application --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT` |
| **Plan** | **Free** ✅ |

6. Click **Create Web Service**
7. Render va a buildear el proyecto (tarda 2-3 minutos)
8. Cuando diga **"Live"** en verde → está funcionando ✅

---

### PASO 5 — Acceder al dashboard

- Render te da una URL del tipo: `https://apex-bot-xxxx.onrender.com`
- Abrirla desde el navegador (PC o celular)
- El bot empieza a operar automáticamente

> ⚠️ **Plan gratuito de Render**: el servicio se "duerme" después de 15 minutos sin visitas.
> Para mantenerlo activo 24/7 sin pagar, usar [UptimeRobot](https://uptimerobot.com) (ver PASO 6).

---

### PASO 6 — Mantener activo 24/7 gratis con UptimeRobot

1. Crear cuenta gratis en [uptimerobot.com](https://uptimerobot.com)
2. Dashboard → **Add New Monitor**
3. Completar:
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: APEX Bot
   - **URL**: `https://apex-bot-xxxx.onrender.com` (tu URL de Render)
   - **Monitoring Interval**: 5 minutes
4. Click **Create Monitor**

UptimeRobot va a hacer un ping cada 5 minutos → el bot nunca se duerme ✅

---

## ⚙️ Parámetros del bot

| Parámetro | Valor |
|-----------|-------|
| Capital inicial | $10,000 |
| Margen por trade | $100 |
| Leverage | 10x ($1,000 notional) |
| Fee por lado | 0.05% |
| Take Profit | 0.1% |
| Stop Loss | 0.1% |
| Max trades abiertos | 5 |
| Cooldown entre trades | 2 minutos por símbolo |
| Intervalo de velas | 5 minutos |

## 📊 Estrategia

- **EMA 9 / EMA 21**: dirección de tendencia
- **RSI 14**: filtro de sobrecompra/sobreventa
- **MACD histogram**: confirmación de momentum

**LONG**: EMA9 > EMA21 + MACD histograma > 0 + RSI entre 40-65  
**SHORT**: EMA9 < EMA21 + MACD histograma < 0 + RSI entre 35-60

---

## 🔧 Ajustar parámetros

Para cambiar TP/SL, editar `bot2/strategy.py`:
```python
TP_PCT = 0.001   # 0.1% → cambiar a 0.002 para 0.2%
SL_PCT = 0.001   # 0.1%
```

Para cambiar capital o leverage, editar `bot2/portfolio.py`:
```python
INITIAL_CAPITAL  = 10_000.0
SIZE_PER_TRADE   = 100.0
LEVERAGE         = 10
```

Después de cualquier cambio: hacer commit en GitHub → Render redeploya automáticamente.
