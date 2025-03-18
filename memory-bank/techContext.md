# Tech Context: Trading Bot

## Tecnologías Utilizadas

### Lenguaje Principal
- **Python 3.10**: Lenguaje principal de desarrollo, elegido por su facilidad de uso, amplia comunidad y excelentes bibliotecas para análisis de datos y aprendizaje automático.

### Bibliotecas Clave
- **ccxt**: Biblioteca unificada para interactuar con múltiples exchanges de criptomonedas.
- **pandas**: Manipulación y análisis de datos estructurados.
- **numpy**: Computación numérica eficiente.
- **matplotlib**: Visualización de datos y gráficos.
- **scipy**: Funciones científicas y estadísticas.
- **pydantic**: Validación de datos y configuraciones.
- **pandera**: Validación de DataFrames.
- **python-dotenv**: Gestión de variables de entorno.
- **schedule**: Programación de tareas recurrentes.
- **tqdm**: Barras de progreso para operaciones largas.
- **binance-historical-data**: Descarga de datos históricos de Binance.

### Herramientas de Desarrollo
- **Docker**: Contenedorización para despliegue consistente.
- **Git**: Control de versiones.

## Configuración de Desarrollo

### Estructura del Proyecto
```
trading_bot/
├── .env                    # Variables de entorno (credenciales API)
├── .gitignore              # Archivos ignorados por git
├── requirements.txt        # Dependencias del proyecto
├── Dockerfile              # Configuración para Docker
├── bitget_bot.py           # Punto de entrada para el bot de Bitget
├── trader.py               # Clase principal de trading
├── exchange_apis.py        # Interfaces para exchanges
├── indicators.py           # Implementación de indicadores técnicos
├── data_manager.py         # Gestión de datos históricos
├── definitions.py          # Definiciones de tipos y estructuras
├── strategies/             # Implementaciones de estrategias
│   ├── __init__.py
│   ├── strategy.py         # Clase base para estrategias
│   ├── multi_moving_average_strategy.py
│   ├── adaptive_moving_average_strategy.py
│   └── momentum_rsi_strategy.py
├── backtesting/            # Sistema de backtesting
│   ├── __init__.py
│   ├── backtester.py       # Simulador de backtesting
│   ├── multi_backtest.py   # Backtesting múltiple
│   └── experiments_manager.py # Gestión de experimentos
├── drawer/                 # Visualización
│   ├── __init__.py
│   ├── backtest_drawer.py  # Visualización de backtests
│   └── indicator_drawer.py # Visualización de indicadores
├── backtests/              # Scripts de backtesting
│   ├── backtest_*.py       # Backtests individuales
│   └── experiment_*.py     # Experimentos
├── data/                   # Datos históricos
│   └── coinex_pairs.txt    # Lista de pares de Coinex
└── tests/                  # Pruebas unitarias
    ├── __init__.py
    └── test_backtester.py  # Pruebas para el backtester
```

### Variables de Entorno
El proyecto utiliza un archivo `.env` para gestionar credenciales y configuraciones sensibles:

```
# Credenciales de Binance
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret

# Credenciales de Bitget
BITGET_API_KEY=your_bitget_api_key
BITGET_API_SECRET=your_bitget_api_secret
BITGET_API_PASSWORD=your_bitget_api_password

# Credenciales de Kraken
KRAKEN_API_KEY=your_kraken_api_key
KRAKEN_API_SECRET=your_kraken_api_secret

# Credenciales de OKX
OKX_API_KEY=your_okx_api_key
OKX_API_SECRET=your_okx_api_secret
OKX_PASSWORD=your_okx_password

# Credenciales específicas para bots
BITGET_API_KEY_DOG_USDT_BOT=specific_bot_api_key
BITGET_API_SECRET_DOG_USDT_BOT=specific_bot_api_secret
```

## Restricciones Técnicas

### Limitaciones de API
- **Rate Limits**: Los exchanges imponen límites en el número de solicitudes por minuto/segundo.
- **Tamaño Mínimo de Orden**: Cada exchange tiene requisitos mínimos para el tamaño de las órdenes.
- **Precisión de Precios**: Los precios deben ajustarse a la precisión específica de cada par de trading.

### Rendimiento
- **Latencia**: La latencia en la comunicación con los exchanges puede afectar la ejecución de estrategias.
- **Procesamiento de Datos**: El análisis de grandes conjuntos de datos históricos puede ser intensivo en recursos.

### Seguridad
- **Gestión de Credenciales**: Las claves API deben mantenerse seguras y nunca incluirse en el control de versiones.
- **Permisos de API**: Se recomienda utilizar claves API con permisos mínimos necesarios (solo lectura cuando sea posible).

## Dependencias Externas

### Exchanges Soportados
- **Binance**: Exchange global con alta liquidez y amplia gama de criptomonedas.
- **Bitget**: Exchange con enfoque en derivados y trading spot.
- **Kraken**: Exchange establecido con buena reputación de seguridad.
- **OKX**: Exchange con amplia gama de productos de trading.

### Fuentes de Datos
- **Binance Historical Data**: Biblioteca para descargar datos históricos de Binance.
- **Coinex Data**: Datos históricos descargados directamente de Coinex.

## Entorno de Ejecución

### Local
Para ejecutar el proyecto localmente:
1. Clonar el repositorio
2. Instalar dependencias: `pip install -r requirements.txt`
3. Crear archivo `.env` con credenciales
4. Ejecutar el bot: `python bitget_bot.py`

### Docker
Para ejecutar con Docker:
1. Construir la imagen: `docker build -t trading_bot .`
2. Ejecutar el contenedor: `docker run --env-file .env trading_bot`

## Consideraciones de Despliegue

### Monitoreo
- Implementar logging detallado para seguimiento de operaciones
- Considerar alertas para eventos críticos (errores de API, problemas de conectividad)

### Respaldo
- Mantener copias de seguridad de datos históricos
- Documentar configuraciones de estrategias exitosas

### Escalabilidad
- El sistema puede escalar horizontalmente ejecutando múltiples instancias para diferentes pares/estrategias
- Considerar la separación de backtesting (intensivo en CPU) y trading en vivo (requiere baja latencia)

## Roadmap Técnico

### Mejoras Potenciales
1. **Implementación de WebSockets**: Para datos de mercado en tiempo real con menor latencia
2. **Base de Datos**: Migrar de archivos CSV a una base de datos para mejor gestión de datos históricos
3. **API REST**: Implementar una API para monitoreo y control remoto
4. **Integración con ML**: Incorporar modelos de aprendizaje automático para predicción de precios
5. **Interfaz Web**: Desarrollar un dashboard para visualización y control
