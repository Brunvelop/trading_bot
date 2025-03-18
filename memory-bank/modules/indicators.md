# Módulo: indicators.py

## Descripción General

El módulo `indicators.py` proporciona una colección de indicadores técnicos utilizados en estrategias de trading. Estos indicadores son herramientas fundamentales para el análisis técnico y la toma de decisiones en el trading algorítmico.

El módulo está diseñado con un enfoque modular y extensible, permitiendo:
- Cálculo estandarizado de indicadores técnicos comunes
- Interfaz consistente para todos los indicadores
- Fácil integración con estrategias de trading
- Extensibilidad para añadir nuevos indicadores

## Estructura del Módulo

### Clases Principales

#### `IndicatorTypes`

Clase contenedora para enumeraciones de tipos de indicadores, organizados en categorías lógicas:

1. **Price**: Indicadores basados en el precio
   - `SIMPLE_MOVING_AVERAGE`: Media móvil simple
   - `BOLLINGER_BANDS`: Bandas de Bollinger
   - `MACD`: Moving Average Convergence Divergence

2. **Extra**: Indicadores adicionales no directamente basados en el precio
   - `VELOCITY`: Velocidad (tasa de cambio)
   - `ACCELERATION`: Aceleración (tasa de cambio de la velocidad)
   - `RELATIVE_STRENGTH_INDEX`: Índice de fuerza relativa (RSI)
   - `VOLUME_SMA`: Media móvil simple del volumen

#### `Indicator`

Clase que proporciona un contenedor estándar para los datos de indicadores:

```python
class Indicator(BaseModel):
    name: str  # Identificador único para el indicador
    type: Union[IndicatorTypes.Price, IndicatorTypes.Extra]  # Categoría y tipo del indicador
    result: pd.Series  # Serie que contiene los valores calculados del indicador
```

Esta clase estandariza la interfaz para todos los indicadores, facilitando su uso en estrategias y visualizaciones.

#### `Indicators`

Clase principal que contiene métodos estáticos para calcular diversos indicadores técnicos:

```python
class Indicators:
    @staticmethod
    def calculate_moving_average(data, window): ...
    
    @staticmethod
    def calculate_bollinger_bands(data, window, num_std): ...
    
    @staticmethod
    def calculate_macd(data, fast_period, slow_period, signal_period): ...
    
    # Otros métodos para diferentes indicadores
```

## Indicadores Implementados

### Indicadores de Precio

1. **Media Móvil Simple (SMA)**
   - Método: `calculate_moving_average(data, window)`
   - Descripción: Calcula el promedio de precios de cierre durante un período específico
   - Uso: Identificar tendencias y niveles de soporte/resistencia

2. **Media Móvil Exponencial (EMA)**
   - Método: `calculate_exponential_moving_average(data, window)`
   - Descripción: Similar a SMA pero da más peso a los precios recientes
   - Uso: Identificar tendencias con mayor sensibilidad a cambios recientes

3. **Bandas de Bollinger**
   - Método: `calculate_bollinger_bands(data, window, num_std)`
   - Descripción: Crea tres bandas (media, superior e inferior) basadas en la volatilidad
   - Uso: Identificar condiciones de sobrecompra/sobreventa y volatilidad

4. **MACD (Moving Average Convergence Divergence)**
   - Método: `calculate_macd(data, fast_period, slow_period, signal_period)`
   - Descripción: Calcula la diferencia entre dos EMAs y su línea de señal
   - Uso: Identificar cambios de tendencia y momentum

### Indicadores Adicionales

1. **RSI (Relative Strength Index)**
   - Método: `calculate_rsi(data, window)`
   - Descripción: Mide la magnitud de los cambios recientes de precio
   - Uso: Identificar condiciones de sobrecompra/sobreventa (>70 / <30)

2. **ATR (Average True Range)**
   - Método: `calculate_atr(data, window)`
   - Descripción: Mide la volatilidad del mercado
   - Uso: Determinar tamaños de stop loss y objetivos de precio

3. **Volumen SMA**
   - Método: `calculate_volume_sma(data, window)`
   - Descripción: Calcula la media móvil del volumen
   - Uso: Identificar tendencias de volumen y confirmar movimientos de precio

4. **Velocidad y Aceleración**
   - Métodos: `calculate_velocity(series, window)` y `calculate_acceleration(velocity, window)`
   - Descripción: Miden la tasa de cambio y la tasa de cambio de la tasa de cambio
   - Uso: Identificar fortalecimiento o debilitamiento de tendencias

## Patrones de Uso

### Cálculo de Indicadores

```python
# Calcular una media móvil simple de 20 períodos
sma = Indicators.calculate_moving_average(market_data, 20)

# Calcular bandas de Bollinger
bands = Indicators.calculate_bollinger_bands(market_data, 20, 2.0)
middle_band, upper_band, lower_band = bands

# Calcular MACD
macd_indicators = Indicators.calculate_macd(market_data)
macd_line, signal_line, histogram = macd_indicators

# Calcular RSI
rsi = Indicators.calculate_rsi(market_data, 14)
```

### Uso en Estrategias

Los indicadores se utilizan típicamente en el método `calculate_indicators` de las estrategias:

```python
def calculate_indicators(self, data):
    indicators = []
    
    # Calcular medias móviles
    indicators.append(Indicators.calculate_moving_average(data, 50))
    indicators.append(Indicators.calculate_moving_average(data, 200))
    
    # Calcular RSI
    indicators.append(Indicators.calculate_rsi(data, 14))
    
    # Calcular MACD
    indicators.extend(Indicators.calculate_macd(data))
    
    return indicators
```

### Toma de Decisiones

Los indicadores se utilizan para tomar decisiones de trading en el método `run` de las estrategias:

```python
def run(self, data, memory):
    actions = []
    
    # Obtener valores de indicadores
    sma_50 = next(i for i in self.indicators if i.name == 'ma_50').result.iloc[-1]
    sma_200 = next(i for i in self.indicators if i.name == 'ma_200').result.iloc[-1]
    rsi = next(i for i in self.indicators if i.name == 'rsi_14').result.iloc[-1]
    
    # Lógica de trading basada en indicadores
    if sma_50 > sma_200 and rsi < 30:
        # Señal de compra
        actions.append(Action(action_type=ActionType.BUY_MARKET, price=data['close'].iloc[-1], amount=1.0))
    elif sma_50 < sma_200 and rsi > 70:
        # Señal de venta
        actions.append(Action(action_type=ActionType.SELL_MARKET, price=data['close'].iloc[-1], amount=1.0))
    
    return actions
```

## Consideraciones Técnicas

### Rendimiento

- Los cálculos de indicadores utilizan operaciones vectorizadas de pandas para un rendimiento óptimo
- Los métodos están diseñados para ser eficientes incluso con grandes conjuntos de datos
- Los resultados se almacenan como Series de pandas para facilitar operaciones posteriores

### Manejo de Valores NaN

- Los primeros valores de muchos indicadores serán NaN debido a las ventanas móviles
- Las estrategias deben manejar adecuadamente estos valores NaN, especialmente al inicio de los datos

### Extensibilidad

El módulo está diseñado para ser fácilmente extensible:

1. Para añadir un nuevo indicador:
   - Implementar un nuevo método estático en la clase `Indicators`
   - Devolver un objeto `Indicator` con un nombre único y tipo apropiado
   - Documentar el indicador con docstrings completos

2. Para añadir una nueva categoría de indicadores:
   - Añadir una nueva clase de enumeración en `IndicatorTypes`
   - Actualizar la anotación de tipo en la clase `Indicator`

## Pruebas

El módulo cuenta con pruebas unitarias completas en `tests/test_indicators.py` que verifican:

- Cálculos correctos de todos los indicadores
- Manejo adecuado de casos límite
- Conformidad con la interfaz esperada

## Mejoras Futuras

1. **Nuevos Indicadores**:
   - Ichimoku Cloud
   - Fibonacci Retracement
   - Stochastic Oscillator
   - On-Balance Volume (OBV)

2. **Optimizaciones**:
   - Implementación de caché para cálculos repetitivos
   - Paralelización para conjuntos de datos muy grandes

3. **Extensiones**:
   - Indicadores personalizables con parámetros adicionales
   - Combinaciones de indicadores para señales compuestas
   - Visualizaciones integradas para cada indicador
