# Segundos fornecidos
segundos = [23952, 15722, 20168]

# Somar os segundos
total_segundos = sum(segundos)

# Converter para horas, minutos e segundos
horas = total_segundos // 3600
minutos = (total_segundos % 3600) // 60
segundos_restantes = total_segundos % 60

# Resultado em formato de hora
horario_normal = f"{horas:02}:{minutos:02}:{segundos_restantes:02}"
print(horario_normal)
