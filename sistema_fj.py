import logging
from abc import ABC, abstractmethod

# ============================================================
# CONFIGURACIÓN DEL SISTEMA DE REGISTRO (LOGS)
# ============================================================
# Se configura un archivo llamado logs.txt donde se almacenarán eventos importantes del sistema como errores y registros


logging.basicConfig(
    filename='logs.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ============================================================
# EXCEPCIONES PERSONALIZADAS
# ============================================================
# Estas clases permiten manejar errores específicos del sistema y diferenciar los problemas


class ValidationError(Exception):
    pass  # Error cuando un dato ingresado no cumple validaciones

class ReservaError(Exception):
    pass  # Error relacionado con reservas

class OperacionNoPermitidaError(Exception):
    pass  # Error cuando una operación genera un resultado inválido

# ============================================================
# CLASE ABSTRACTA BASE
# ============================================================
# Sirve como plantilla obligatoria para otras clases.

class Entidad(ABC):

    @abstractmethod
    def obtener_detalles(self):
        pass


# ============================================================
# CLASE CLIENTE
# ============================================================
# Representa a un cliente del sistema.

class Cliente(Entidad):

    def __init__(self, identificacion, nombre, email):
        self.identificacion = identificacion
        self.nombre = nombre
        self.email = email

    # Getter y setter para identificación
    @property
    def identificacion(self):
        return self._identificacion

    @identificacion.setter
    def identificacion(self, valor):
        # Verifica que sea texto válido
        if not isinstance(valor, str) or not valor.strip():
            raise ValidationError("Identificación debe ser texto válido.")
        self._identificacion = valor

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        # Exige mínimo 3 caracteres
        if len(valor.strip()) < 3:
            raise ValidationError("Nombre debe tener mínimo 3 caracteres.")
        self._nombre = valor

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, valor):
        # Validación básica de correo
        if "@" not in valor:
            raise ValidationError("Correo electrónico no válido.")
        self._email = valor

    def obtener_detalles(self):
        return f"Cliente: {self.nombre} | ID: {self.identificacion} | Email: {self.email}"


# ============================================================
# CLASE ABSTRACTA SERVICIO
# ============================================================
# Base para todos los tipos de servicios disponibles.
# Obliga a implementar cálculo de costo.
class Servicio(Entidad):

    def __init__(self, nombre_servicio, tarifa_base):
        self.nombre_servicio = nombre_servicio
        self.tarifa_base = tarifa_base

    @abstractmethod
    def calcular_costo_final(self, tiempo, impuesto=0, descuento=0):
        pass


# ============================================================
# SERVICIO: RESERVA DE SALA
# ============================================================
class ReservaSala(Servicio):

    def calcular_costo_final(self, horas, impuesto=0, descuento=0):
        try:
            # Validar que las horas sean positivas
            if horas <= 0:
                raise ValueError("Las horas deben ser mayores a cero.")

            # Cálculo base
            subtotal = self.tarifa_base * horas

            # Aplicar impuesto y descuento
            total = subtotal + subtotal * impuesto - descuento

            # Evitar costos negativos
            if total < 0:
                raise OperacionNoPermitidaError("El costo no puede ser negativo.")

            return total

        except ValueError as e:
            # Convierte error genérico en uno específico del sistema
            raise ReservaError("Error en la reserva de sala.") from e

    def obtener_detalles(self):
        return f"Reserva Sala: {self.nombre_servicio} - ${self.tarifa_base}/hora"


# ============================================================
# SERVICIO: ALQUILER DE EQUIPO
# ============================================================
class AlquilerEquipo(Servicio):

    def calcular_costo_final(self, dias, impuesto=0, descuento=0):

        if dias <= 0:
            raise ReservaError("Los días deben ser mayores a cero.")

        subtotal = self.tarifa_base * dias
        total = subtotal + subtotal * impuesto - descuento

        if total < 0:
            raise OperacionNoPermitidaError("Costo inválido.")

        return total

    def obtener_detalles(self):
        return f"Alquiler Equipo: {self.nombre_servicio} - ${self.tarifa_base}/día"


# ============================================================
# SERVICIO: ASESORÍA ESPECIALIZADA
# ============================================================
class AsesoriaEspecializada(Servicio):

    def calcular_costo_final(self, sesiones, impuesto=0, descuento=0):

        if sesiones <= 0:
            raise ReservaError("Las sesiones deben ser mayores a cero.")

        # Tiene un cargo fijo adicional
        subtotal = (self.tarifa_base * sesiones) + 50

        total = subtotal + subtotal * impuesto - descuento

        if total < 0:
            raise OperacionNoPermitidaError("Costo inválido.")

        return total

    def obtener_detalles(self):
        return f"Asesoría: {self.nombre_servicio} - ${self.tarifa_base}/sesión + $50 fijo"


# ============================================================
# CLASE RESERVA
# ============================================================
# Une cliente + servicio + cantidad solicitada
class Reserva:

    def __init__(self, cliente, servicio, cantidad):

        # Validación de tipos
        if not isinstance(cliente, Cliente):
            raise ValidationError("Cliente inválido.")

        if not isinstance(servicio, Servicio):
            raise ValidationError("Servicio inválido.")

        self.cliente = cliente
        self.servicio = servicio
        self.cantidad = cantidad
        self.estado = "PENDIENTE"

    def procesar_reserva(self, impuesto=0, descuento=0):

        try:
            # Calcula el costo usando el método del servicio específico
            costo = self.servicio.calcular_costo_final(
                self.cantidad,
                impuesto,
                descuento
            )

        except Exception as e:
            # Si ocurre error, se marca como fallida
            self.estado = "FALLIDA"
            logging.error(f"Error al procesar reserva: {e}")
            raise

        else:
            # Si todo sale bien
            self.estado = "CONFIRMADA"
            logging.info(f"Reserva confirmada para {self.cliente.nombre}")
            return costo

        finally:
            # Siempre registra estado final
            logging.info(f"Estado final reserva: {self.estado}")

    def obtener_detalles(self):
        return f"{self.cliente.nombre} | {self.servicio.nombre_servicio} | Estado: {self.estado}"


# ============================================================
# SISTEMA PRINCIPAL
# ============================================================
# Administra clientes, servicios y reservas
class SistemaGestion:

    def __init__(self):
        self.clientes = []
        self.reservas = []

        # Catálogo de servicios
        self.servicios = [
            ReservaSala("Sala de Juntas", 100),
            AlquilerEquipo("Portátil", 80),
            AsesoriaEspecializada("Seguridad Informática", 200)
        ]

    def registrar_cliente(self, identificacion, nombre, email):

        # Evita clientes duplicados
        if any(c.identificacion == identificacion for c in self.clientes):
            raise ValidationError("Ya existe un cliente con ese ID.")

        cliente = Cliente(identificacion, nombre, email)
        self.clientes.append(cliente)

        logging.info(f"Cliente registrado: {cliente.nombre}")
        return cliente

    def buscar_cliente(self, identificacion):

        for cliente in self.clientes:
            if cliente.identificacion == identificacion:
                return cliente

        raise ValidationError("Cliente no encontrado.")

    def crear_reserva(self, identificacion_cliente, indice_servicio, cantidad):

        cliente = self.buscar_cliente(identificacion_cliente)

        # Verifica índice válido
        if indice_servicio < 0 or indice_servicio >= len(self.servicios):
            raise ValidationError("Servicio inválido.")

        servicio = self.servicios[indice_servicio]

        reserva = Reserva(cliente, servicio, cantidad)

        costo = reserva.procesar_reserva()

        self.reservas.append(reserva)

        return reserva, costo


# ============================================================
# SIMULACIÓN AUTOMÁTICA
# ============================================================
# Ejecuta pruebas para validar funcionamiento
def simulacion():
    sistema = SistemaGestion()

    pruebas = [
        lambda: sistema.registrar_cliente("1", "Carlos Perez", "carlos@mail.com"),
        lambda: sistema.registrar_cliente("2", "Ana", "ana@mail.com"),
        lambda: sistema.registrar_cliente("1", "Duplicado", "dup@mail.com"),
        lambda: sistema.crear_reserva("1", 0, 3),
    ]

    for i, prueba in enumerate(pruebas, start=1):
        try:
            print(f"\nOperación {i}")
            resultado = prueba()
            print("Éxito:", resultado)

        except Exception as e:
            print("Error controlado:", e)


# ============================================================
# MENÚ INTERACTIVO
# ============================================================
# Interfaz de consola para interactuar con el sistema
def menu():
    sistema = SistemaGestion()

    while True:
        print("\n===== SOFTWARE FJ =====")
        print("1. Registrar cliente")
        print("2. Crear una reserva")
        print("3. Listar clientes")
        print("4. Listar reservas")
        print("5. Simulación")
        print("6. Salir")

        opcion = input("Seleccione opción: ")

        if opcion == "6":
            break


# ============================================================
# PUNTO DE ENTRADA
# ============================================================
# Ejecuta el menú solo si el archivo se ejecuta directamente
if __name__ == "__main__":
    menu()
